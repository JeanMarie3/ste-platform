[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [string]$ServerHost,

    [string]$ServerUser = 'root',
    [string]$RemoteProjectPath = '/opt/ste-platform',
    [string]$RemoteComposeFile = 'docker-compose.prod.yml',

    [string]$DbUser = 'ste_user',
    [string]$DbName = 'ste_platform',

    [switch]$IncludeUsers,
    [switch]$SkipBackup,
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'

function Test-RequiredTool {
    param([Parameter(Mandatory = $true)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required tool '$Name' was not found in PATH."
    }
}

function Get-TableList {
    param([switch]$IncludeUsers)

    $tables = @('requirements', 'test_cases', 'test_runs')
    if ($IncludeUsers) {
        return @('users') + $tables
    }
    return $tables
}

function New-CountSql {
    param([string[]]$Tables)

    $parts = foreach ($table in $Tables) {
        "SELECT '$table' AS table_name, COUNT(*) AS row_count FROM $table"
    }
    return ($parts -join ' UNION ALL ') + ';'
}

function Read-CountMap {
    param([string[]]$Lines)

    $map = @{}
    foreach ($line in $Lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $split = $line -split '\|'
        if ($split.Count -ne 2) {
            continue
        }

        $name = $split[0].Trim()
        $value = $split[1].Trim()
        if (-not [string]::IsNullOrWhiteSpace($name) -and $value -match '^\d+$') {
            $map[$name] = [int]$value
        }
    }
    return $map
}

function Show-Counts {
    param(
        [string]$Title,
        [hashtable]$Counts,
        [string[]]$Tables
    )

    Write-Host ""
    Write-Host $Title -ForegroundColor Cyan
    foreach ($table in $Tables) {
        $value = if ($Counts.ContainsKey($table)) { $Counts[$table] } else { 'n/a' }
        Write-Host ("- {0}: {1}" -f $table, $value)
    }
}

Test-RequiredTool -Name 'docker'
Test-RequiredTool -Name 'ssh'

$tables = Get-TableList -IncludeUsers:$IncludeUsers
$tableArgs = foreach ($table in $tables) { "--table=$table" }
$countSql = New-CountSql -Tables $tables
$target = "$ServerUser@$ServerHost"
$utcStamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$remoteBackupFile = "/root/prod-before-sync-$utcStamp.dump"

$remotePsql = "cd $RemoteProjectPath && docker compose -f $RemoteComposeFile exec -T postgres psql -v ON_ERROR_STOP=1 -U $DbUser -d $DbName"
$remotePsqlAt = "cd $RemoteProjectPath && docker compose -f $RemoteComposeFile exec -T postgres psql -v ON_ERROR_STOP=1 -At -F '|' -U $DbUser -d $DbName"
$remoteBackup = "cd $RemoteProjectPath && docker compose -f $RemoteComposeFile exec -T postgres pg_dump -U $DbUser -d $DbName -Fc > $remoteBackupFile"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STE Platform - Sync Local DB to Prod" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Remote target: $target" -ForegroundColor Yellow
Write-Host "Remote stack: $RemoteProjectPath/$RemoteComposeFile" -ForegroundColor Yellow
Write-Host "Tables: $($tables -join ', ')" -ForegroundColor Yellow
if (-not $IncludeUsers) {
    Write-Host "Note: users table is excluded by default (use -IncludeUsers to include it)." -ForegroundColor DarkYellow
}

if ($ValidateOnly) {
    Write-Host ""
    Write-Host "[OK] Validation passed. Tools found and script configuration is ready." -ForegroundColor Green
    return
}

Write-Host ""
Write-Host "Step 1/5: Reading local counts..." -ForegroundColor Yellow
$localCountLines = & docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -At -F '|' -U $DbUser -d $DbName -c $countSql
$localCounts = Read-CountMap -Lines $localCountLines
Show-Counts -Title 'Local counts' -Counts $localCounts -Tables $tables

Write-Host ""
Write-Host "Step 2/5: Reading remote counts before sync..." -ForegroundColor Yellow
$remoteBeforeLines = $countSql | & ssh $target $remotePsqlAt
$remoteBeforeCounts = Read-CountMap -Lines $remoteBeforeLines
Show-Counts -Title 'Remote counts (before)' -Counts $remoteBeforeCounts -Tables $tables

if (-not $SkipBackup) {
    if ($PSCmdlet.ShouldProcess($target, "Create remote backup at $remoteBackupFile")) {
        Write-Host ""
        Write-Host "Step 3/5: Creating remote backup..." -ForegroundColor Yellow
        & ssh $target $remoteBackup
        Write-Host "[OK] Remote backup created: $remoteBackupFile" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "Step 3/5: Skipping remote backup (-SkipBackup)." -ForegroundColor DarkYellow
}

if ($PSCmdlet.ShouldProcess($target, 'Truncate target tables before import')) {
    Write-Host ""
    Write-Host "Step 4/5: Truncating remote tables..." -ForegroundColor Yellow
    $truncateSql = "TRUNCATE TABLE $($tables -join ', ') RESTART IDENTITY CASCADE;"
    $truncateSql | & ssh $target $remotePsql
    Write-Host "[OK] Remote tables truncated" -ForegroundColor Green
}

if ($PSCmdlet.ShouldProcess($target, 'Stream local dump into remote database')) {
    Write-Host ""
    Write-Host "Step 5/5: Streaming local data to remote..." -ForegroundColor Yellow
    & docker compose exec -T postgres pg_dump -U $DbUser -d $DbName --data-only --no-owner --no-privileges @tableArgs |
        & ssh $target $remotePsql
    Write-Host "[OK] Data stream completed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Verification: Reading remote counts after sync..." -ForegroundColor Yellow
$remoteAfterLines = $countSql | & ssh $target $remotePsqlAt
$remoteAfterCounts = Read-CountMap -Lines $remoteAfterLines
Show-Counts -Title 'Remote counts (after)' -Counts $remoteAfterCounts -Tables $tables

$allMatch = $true
foreach ($table in $tables) {
    $localValue = if ($localCounts.ContainsKey($table)) { $localCounts[$table] } else { -1 }
    $remoteValue = if ($remoteAfterCounts.ContainsKey($table)) { $remoteAfterCounts[$table] } else { -2 }
    if ($localValue -ne $remoteValue) {
        $allMatch = $false
        Write-Host ("[WARN] Count mismatch for {0}: local={1}, remote={2}" -f $table, $localValue, $remoteValue) -ForegroundColor Yellow
    }
}

if ($allMatch) {
    Write-Host ""
    Write-Host "[OK] Sync completed and counts match." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[WARN] Sync finished, but counts differ. Review output and optionally restore backup: $remoteBackupFile" -ForegroundColor Yellow
}


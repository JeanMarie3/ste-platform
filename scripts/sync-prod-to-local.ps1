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
$localBackupFile = "$PWD/local-before-sync-$utcStamp.dump"

$remotePsqlAt = "cd $RemoteProjectPath && docker compose -f $RemoteComposeFile exec -T postgres psql -v ON_ERROR_STOP=1 -At -F '|' -U $DbUser -d $DbName"
$remoteBackup = "cd $RemoteProjectPath && docker compose -f $RemoteComposeFile exec -T postgres pg_dump -U $DbUser -d $DbName --data-only --no-owner --no-privileges $($tableArgs -join ' ')"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STE Platform - Sync Prod DB to Local" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Remote source: $target" -ForegroundColor Yellow
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
Write-Host "Step 1/5: Reading remote counts from production..." -ForegroundColor Yellow
$remoteCountLines = $countSql | & ssh $target $remotePsqlAt
$remoteCounts = Read-CountMap -Lines $remoteCountLines
Show-Counts -Title 'Remote Prod counts' -Counts $remoteCounts -Tables $tables

Write-Host ""
Write-Host "Step 2/5: Reading local counts before sync..." -ForegroundColor Yellow
$localBeforeLines = & docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -At -F '|' -U $DbUser -d $DbName -c $countSql
$localBeforeCounts = Read-CountMap -Lines $localBeforeLines
Show-Counts -Title 'Local counts (before)' -Counts $localBeforeCounts -Tables $tables

if (-not $SkipBackup) {
    if ($PSCmdlet.ShouldProcess("Local Database", "Create local backup at $localBackupFile")) {
        Write-Host ""
        Write-Host "Step 3/5: Creating local backup..." -ForegroundColor Yellow
        & docker compose exec -T postgres pg_dump -U $DbUser -d $DbName -Fc > $localBackupFile
        Write-Host "[OK] Local backup created: $localBackupFile" -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "Step 3/5: Skipping local backup (-SkipBackup)." -ForegroundColor DarkYellow
}

if ($PSCmdlet.ShouldProcess("Local Database", 'Truncate local tables before import')) {
    Write-Host ""
    Write-Host "Step 4/5: Truncating local tables..." -ForegroundColor Yellow
    $truncateSql = "TRUNCATE TABLE $($tables -join ', ') RESTART IDENTITY CASCADE;"
    & docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U $DbUser -d $DbName -c $truncateSql
    Write-Host "[OK] Local tables truncated" -ForegroundColor Green
}

if ($PSCmdlet.ShouldProcess("Local Database", 'Stream Prod dump into local database')) {
    Write-Host ""
    Write-Host "Step 5/5: Streaming remote Prod data to local dev environment..." -ForegroundColor Yellow
    & ssh $target $remoteBackup | & docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U $DbUser -d $DbName
    Write-Host "[OK] Data stream completed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Verification: Reading local counts after sync..." -ForegroundColor Yellow
$localAfterLines = & docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -At -F '|' -U $DbUser -d $DbName -c $countSql
$localAfterCounts = Read-CountMap -Lines $localAfterLines
Show-Counts -Title 'Local counts (after)' -Counts $localAfterCounts -Tables $tables

$allMatch = $true
foreach ($table in $tables) {
    $remoteValue = if ($remoteCounts.ContainsKey($table)) { $remoteCounts[$table] } else { -1 }
    $localValue = if ($localAfterCounts.ContainsKey($table)) { $localAfterCounts[$table] } else { -2 }
    if ($remoteValue -ne $localValue) {
        $allMatch = $false
        Write-Host ("[WARN] Count mismatch for {0}: remote={1}, local={2}" -f $table, $remoteValue, $localValue) -ForegroundColor Yellow
    }
}

if ($allMatch) {
    Write-Host ""
    Write-Host "[OK] Prod -> Local Sync completed and counts match." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[WARN] Sync finished, but counts differ. Review output and optionally restore backup: $localBackupFile" -ForegroundColor Yellow
}

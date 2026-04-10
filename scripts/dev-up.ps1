param(
    [switch]$NoInstall,
    [switch]$ForceReinstall,
    [switch]$SkipBrowserInstall,
    [int]$TimeoutSeconds = 90
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $repoRoot '.run'
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

$backendDir = Join-Path $repoRoot 'backend'
$agentDir = Join-Path $repoRoot 'agent'
$frontendDir = Join-Path $repoRoot 'frontend'
$defaultPostgresUrl = 'postgresql+psycopg://ste_user:ste_password@localhost:5432/ste_platform'

function Assert-CommandAvailable {
    param([Parameter(Mandatory = $true)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

function Ensure-Venv {
    param(
        [Parameter(Mandatory = $true)][string]$ServiceDir,
        [Parameter(Mandatory = $true)][string]$RequirementsFile,
        [switch]$SkipInstall,
        [switch]$Reinstall
    )

    $venvPython = Join-Path $ServiceDir '.venv\Scripts\python.exe'
    if (-not (Test-Path $venvPython)) {
        Write-Host "Creating venv in $ServiceDir"
        & python -m venv (Join-Path $ServiceDir '.venv') | Out-Null
    }

    if (-not $SkipInstall -or $Reinstall) {
        Write-Host "Installing Python dependencies in $ServiceDir"
        & $venvPython -m pip install -r $RequirementsFile | Out-Null
    }

    return $venvPython
}

function Ensure-FrontendDeps {
    param(
        [Parameter(Mandatory = $true)][string]$Dir,
        [switch]$SkipInstall,
        [switch]$Reinstall
    )

    $nodeModules = Join-Path $Dir 'node_modules'
    if ($Reinstall -or (-not $SkipInstall -and -not (Test-Path $nodeModules))) {
        Write-Host 'Installing frontend dependencies'
        Push-Location $Dir
        try {
            & npm install
        }
        finally {
            Pop-Location
        }
    }
}

function Ensure-PlaywrightChromium {
    param(
        [Parameter(Mandatory = $true)][string]$PythonExe,
        [Parameter(Mandatory = $true)][string]$ServiceDir,
        [switch]$SkipInstall,
        [switch]$Reinstall
    )

    if ($SkipInstall) {
        return
    }

    $markerPath = Join-Path $ServiceDir '.playwright-chromium-installed'
    if ($Reinstall -or -not (Test-Path $markerPath)) {
        Write-Host 'Installing Playwright Chromium browser for local agent runs'
        & $PythonExe -m playwright install chromium | Out-Null
        Set-Content -Path $markerPath -Value (Get-Date -Format o) -Encoding UTF8
    }
}

function Assert-LocalPortsFree {
    param([Parameter(Mandatory = $true)][int[]]$Ports)

    foreach ($port in $Ports) {
        $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $listener) {
            continue
        }

        $owner = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        $ownerText = if ($null -ne $owner) { "$($owner.ProcessName) (PID $($owner.Id))" } else { "PID $($listener.OwningProcess)" }

        throw "Port $port is already in use by $ownerText. Stop Docker stack (docker compose down) or the local process before running dev-up."
    }
}

function Start-TrackedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$LogPrefix
    )

    $stdoutPath = Join-Path $runDir "$LogPrefix.out.log"
    $stderrPath = Join-Path $runDir "$LogPrefix.err.log"

    $process = Start-Process -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -NoNewWindow `
        -PassThru

    Write-Host "Started $Name (PID: $($process.Id))"

    Start-Sleep -Milliseconds 800
    if ($process.HasExited) {
        $stderrTail = ''
        if (Test-Path $stderrPath) {
            $stderrTail = (Get-Content -Path $stderrPath -Tail 20 -ErrorAction SilentlyContinue) -join "`n"
        }
        throw "$Name exited immediately after start. Check $stderrPath. $stderrTail"
    }

    [pscustomobject]@{
        name = $Name
        pid = $process.Id
        stdout = $stdoutPath
        stderr = $stderrPath
    }
}

function Wait-ForHttp {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][int]$TimeoutSec
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4 | Out-Null
            return $true
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Ensure-PostgresService {
    param([int]$TimeoutSec = 60)

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host '[WARN] Docker is not available. Local backend may fail if DATABASE_URL points to PostgreSQL.' -ForegroundColor Yellow
        return
    }

    $postgresRunning = (& docker compose ps --status running --services postgres 2>$null) -join "`n"
    if ($postgresRunning -notmatch 'postgres') {
        Write-Host 'Starting Docker postgres service for local data parity...'
        & docker compose up -d postgres | Out-Null
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $health = (& docker inspect -f "{{.State.Health.Status}}" ste-postgres 2>$null).Trim()
            if ($health -eq 'healthy') {
                Write-Host '[OK] Postgres is healthy' -ForegroundColor Green
                return
            }
        }
        catch {
            # keep waiting until timeout
        }
        Start-Sleep -Seconds 1
    }

    throw 'Postgres service did not become healthy in time. Run: docker compose up -d postgres'
}

Assert-CommandAvailable -Name 'python'
Assert-CommandAvailable -Name 'npm'

if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    $env:DATABASE_URL = $defaultPostgresUrl
    Write-Host "Using default DATABASE_URL for local/dev parity: $($env:DATABASE_URL)"
}

if ($env:DATABASE_URL -match '^postgresql(\+[^:]+)?:') {
    Ensure-PostgresService
}

Assert-LocalPortsFree -Ports @(8000, 8010, 5173)

$backendPython = Ensure-Venv -ServiceDir $backendDir -RequirementsFile (Join-Path $backendDir 'requirements.txt') -SkipInstall:$NoInstall -Reinstall:$ForceReinstall
$agentPython = Ensure-Venv -ServiceDir $agentDir -RequirementsFile (Join-Path $agentDir 'requirements.txt') -SkipInstall:$NoInstall -Reinstall:$ForceReinstall
Ensure-PlaywrightChromium -PythonExe $agentPython -ServiceDir $agentDir -SkipInstall:$SkipBrowserInstall -Reinstall:$ForceReinstall
Ensure-FrontendDeps -Dir $frontendDir -SkipInstall:$NoInstall -Reinstall:$ForceReinstall

$npmCommand = (Get-Command npm.cmd -ErrorAction SilentlyContinue)
if ($null -eq $npmCommand) {
    throw 'Could not resolve npm.cmd from PATH'
}

$processes = @()
$processes += Start-TrackedProcess -Name 'backend' -FilePath $backendPython -Arguments @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload') -WorkingDirectory $backendDir -LogPrefix 'backend'
$processes += Start-TrackedProcess -Name 'agent' -FilePath $agentPython -Arguments @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8010', '--reload') -WorkingDirectory $agentDir -LogPrefix 'agent'
$processes += Start-TrackedProcess -Name 'frontend' -FilePath $npmCommand.Source -Arguments @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173') -WorkingDirectory $frontendDir -LogPrefix 'frontend'

$pidsPath = Join-Path $runDir 'pids.json'
$processes | ConvertTo-Json | Set-Content -Path $pidsPath -Encoding UTF8

$checks = @(
    @{ name = 'backend'; url = 'http://127.0.0.1:8000/api/v1/health' },
    @{ name = 'agent'; url = 'http://127.0.0.1:8010/health' },
    @{ name = 'frontend'; url = 'http://127.0.0.1:5173/' }
)

$failed = @()
foreach ($check in $checks) {
    Write-Host "Waiting for $($check.name) -> $($check.url)"
    if (-not (Wait-ForHttp -Url $check.url -TimeoutSec $TimeoutSeconds)) {
        $failed += $check.name
    }
}

if ($failed.Count -gt 0) {
    Write-Host 'One or more services did not become healthy in time.' -ForegroundColor Yellow
    Write-Host "Failed: $($failed -join ', ')"
    Write-Host "See logs in $runDir"
    exit 1
}

Write-Host ''
Write-Host 'All services are running.' -ForegroundColor Green
Write-Host 'Frontend: http://127.0.0.1:5173'
Write-Host 'Backend health: http://127.0.0.1:8000/api/v1/health'
Write-Host 'Agent health: http://127.0.0.1:8010/health'
Write-Host "Logs and PIDs: $runDir"



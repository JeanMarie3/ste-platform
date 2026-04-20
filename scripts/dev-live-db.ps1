[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ServerHost,

    [string]$ServerUser = 'root',
    [int]$RemotePort = 5432,
    [int]$LocalPort = 5433,

    [string]$DbUser = 'ste_user',
    [string]$DbName = 'ste_platform',
    [string]$DbPassword = 'change_me'
)

$ErrorActionPreference = 'Stop'

function Test-RequiredTool {
    param([Parameter(Mandatory = $true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required tool '$Name' was not found in PATH."
    }
}

Test-RequiredTool -Name 'ssh'

$target = "$ServerUser@$ServerHost"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "STE Platform - Dev with Live DB" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating SSH Tunnel: Local IP port $LocalPort -> $target port $RemotePort" -ForegroundColor Yellow

Write-Host "Opening SSH tunnel in a new terminal window..."
$args = "-N -L $LocalPort`:127.0.0.1`:$RemotePort $target"
$sshProcess = Start-Process ssh -ArgumentList $args -PassThru -NoNewWindow:$false

# Prepare environment variable explicitly for this session
$env:DATABASE_URL = "postgresql+psycopg://$DbUser`:$DbPassword@127.0.0.1:$LocalPort/$DbName"
Write-Host "Using remote Database URL equivalent: $($env:DATABASE_URL)" -ForegroundColor Cyan

Write-Host "Starting local Dev services..."
Push-Location $PWD
try {
    Write-Host "For a clean environment, ensure docker stack is down (`.\scripts\docker-down.ps1`)." -ForegroundColor DarkYellow
    . .\scripts\dev-up.ps1 -SkipPostgres
} finally {
    Pop-Location
    Write-Host "Stopping SSH Tunnel..." -ForegroundColor Yellow
    if ($sshProcess -and -not $sshProcess.HasExited) {
        Stop-Process -Id $sshProcess.Id -Force
    }
}

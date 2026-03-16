Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $repoRoot '.run'
$pidsPath = Join-Path $runDir 'pids.json'

function Stop-ProcessTree {
    param([Parameter(Mandatory = $true)][int]$RootPid)

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $RootPid" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -RootPid ([int]$child.ProcessId)
    }

    try {
        Stop-Process -Id $RootPid -Force -ErrorAction Stop
    }
    catch {
        # Already gone.
    }
}

if (Test-Path $pidsPath) {
    $entries = Get-Content -Path $pidsPath -Raw | ConvertFrom-Json
    if ($entries -isnot [System.Array]) {
        $entries = @($entries)
    }

    foreach ($entry in $entries) {
        $targetPid = [int]$entry.pid
        $process = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
        if ($null -ne $process) {
            Stop-ProcessTree -RootPid $targetPid
            Write-Host "Stopped $($entry.name) (PID: $targetPid)"
        }
        else {
            Write-Host "Process not running: $($entry.name) (PID: $targetPid)"
        }
    }

    Remove-Item -Path $pidsPath -Force
}
else {
    Write-Host "No PID file found at $pidsPath"
}

# Extra cleanup: stale listeners can survive if they were orphaned from earlier --reload runs.
$ports = @(8000, 8010, 5173)
foreach ($port in $ports) {
    $listeners = Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($listener in $listeners) {
        $targetPid = [int]$listener.OwningProcess
        try {
            Stop-ProcessTree -RootPid $targetPid
            Write-Host "Stopped stale listener on port $port (PID: $targetPid)"
        }
        catch {
            Write-Host "Could not stop listener on port $port (PID: $targetPid)"
        }
    }
}

Write-Host 'Done.'

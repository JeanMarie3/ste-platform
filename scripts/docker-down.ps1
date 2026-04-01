[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$RemoveVolumes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location "C:\Users\Jean001\source\ste-platform"

$downArgs = @('compose', 'down')
if ($RemoveVolumes) {
    $downArgs += '-v'
}

$commandPreview = "docker $($downArgs -join ' ')"
if ($PSCmdlet.ShouldProcess('Docker compose stack', $commandPreview)) {
    & docker @downArgs
}


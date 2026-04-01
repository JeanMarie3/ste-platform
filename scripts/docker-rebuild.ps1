[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateSet('redeploy', 'rebuild', 'status', 'down')]
    [string]$Action = 'rebuild',
    [switch]$RemoveVolumes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location "C:\Users\Jean001\source\ste-platform"

function Invoke-ComposeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    $commandPreview = "docker $($Args -join ' ')"
    if ($PSCmdlet.ShouldProcess('Docker compose stack', $commandPreview)) {
        & docker @Args
    }
}

switch ($Action) {
    'redeploy' {
        $downArgs = @('compose', 'down')
        if ($RemoveVolumes) {
            $downArgs += '-v'
        }

        # Logical sequence: stop -> rebuild/start -> show status.
        Invoke-ComposeCommand -Args $downArgs
        Invoke-ComposeCommand -Args @('compose', 'up', '-d', '--build')
        Invoke-ComposeCommand -Args @('compose', 'ps')
    }
    'rebuild' {
        Invoke-ComposeCommand -Args @('compose', 'up', '-d', '--build')
        Invoke-ComposeCommand -Args @('compose', 'ps')
    }
    'status' {
        Invoke-ComposeCommand -Args @('compose', 'ps')
    }
    'down' {
        $downArgs = @('compose', 'down')
        if ($RemoveVolumes) {
            $downArgs += '-v'
        }

        Invoke-ComposeCommand -Args $downArgs
    }
}

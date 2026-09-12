# Trusted operator launcher for a per-user Docker Sandboxes installation.
# This configures only this PowerShell process and its children, not the OS.
# Never expose this launcher as a tool inside an untrusted worker.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$SbxArguments = @('version')
)
$ErrorActionPreference = 'Stop'
$runtimeRoot = Join-Path $env:LOCALAPPDATA 'DockerSandboxes'
$executable = Join-Path $runtimeRoot 'bin/sbx.exe'
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw 'Per-user Docker Sandboxes installation not found.'
}
$runtimeTemp = Join-Path $env:LOCALAPPDATA 'DAIA/runtime-temp'
New-Item -ItemType Directory -Force -Path $runtimeTemp | Out-Null
$env:TEMP = $runtimeTemp
$env:TMP = $runtimeTemp
$env:PATH = (Join-Path $runtimeRoot 'bin') + ';' +
    (Join-Path $runtimeRoot 'libexec') + ';' +
    (Join-Path $env:SystemRoot 'System32') + ';' + $env:SystemRoot
$env:PATHEXT = '.COM;.EXE;.BAT;.CMD'
& $executable @SbxArguments
exit $LASTEXITCODE

param([Parameter(Mandatory=$true)][string]$TailnetUrl)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$python = Join-Path $repo '.venv\Scripts\python.exe'
$runtime = Join-Path $repo '.runtime'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Port 8000 is occupied. Inspect the owner before starting DAIA.'
}
# No auto-seeding, invitations, service installation, or tailnet changes on restart.
$process = Start-Process -FilePath $python -WorkingDirectory $repo -WindowStyle Hidden `
    -ArgumentList @('-m', 'daia.cli', '--db', '.runtime/pilot.sqlite3', 'serve-mcp', '--tailnet-url', $TailnetUrl) `
    -RedirectStandardOutput (Join-Path $runtime 'pilot.stdout.log') `
    -RedirectStandardError (Join-Path $runtime 'pilot.stderr.log') -PassThru
$process.Id | Set-Content -LiteralPath (Join-Path $runtime 'pilot.pid')
Write-Output "DAIA process started with PID $($process.Id). Listener: 127.0.0.1:8000. Verify before use."

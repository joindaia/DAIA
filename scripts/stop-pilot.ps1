$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repo '.runtime\pilot.pid'
if (-not (Test-Path -LiteralPath $pidFile)) { throw 'No saved DAIA pilot PID.' }
$pilotProcessId = [int](Get-Content -LiteralPath $pidFile -Raw)
# Windows venv Python may launch a child interpreter. Match both identity and command.
$processes = Get-CimInstance Win32_Process | Where-Object {
    ($_.ProcessId -eq $pilotProcessId -or $_.ParentProcessId -eq $pilotProcessId) -and
    $_.CommandLine -like '*daia.cli*' -and $_.CommandLine -like '*.runtime/pilot.sqlite3*'
}
if (-not $processes) { throw 'Saved DAIA process no longer matches. Nothing was stopped.' }
$processes | Sort-Object ProcessId -Descending | ForEach-Object {
    Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
}
Remove-Item -LiteralPath $pidFile
Write-Output 'Stopped the matching DAIA pilot process. Disable its Serve port separately.'

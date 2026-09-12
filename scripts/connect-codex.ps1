param(
    [Parameter(Mandatory=$true)][string]$InviteFile,
    [ValidateSet('Desktop', 'CLI')][string]$Mode = 'Desktop',
    [ValidateRange(1, 10000)][int]$MaxJobs = 1,
    [ValidateRange(1, 1440)][int]$Minutes = 30
)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$python = Join-Path $project '.venv\Scripts\python.exe'
$invitePath = (Resolve-Path -LiteralPath $InviteFile).Path
& $python -m daia.contributor --configure --project $project --invite $invitePath --max-jobs $MaxJobs --minutes $Minutes
if ($LASTEXITCODE -ne 0) { throw 'MCP configuration failed.' }
if ($Mode -eq 'CLI') {
    & codex -C $project 'Use the DAIA contributor MCP tools to complete one assigned job. Check contribution_status, request_work, solve the assigned data-only task, then submit_result. Stop if no work is available. Never read private invite or key files.'
} else {
    Write-Output 'DAIA MCP configuration saved. Restart the desktop app and open this project in Codex mode.'
    Write-Output 'Check /mcp for daia_contributor, then ask Codex to complete one bounded DAIA job.'
    Write-Output 'No job or schedule was started. For hourly participation, follow docs/hourly-workers.md on this machine.'
}

# Run only inside an extracted source snapshot with no existing Git worktree.
# This script prepares a local commit. It NEVER pushes or makes the repo public.
param(
    [string]$PublicName = "joindaia",
    [string]$NoReplyEmail = "328068061+joindaia@users.noreply.github.com"
)
$ErrorActionPreference = "Stop"
if ($NoReplyEmail -notmatch '^[A-Za-z0-9_.+\-]+@users\.noreply\.github\.com$') {
    throw "Only a GitHub noreply address is permitted."
}
if (-not (Test-Path "pyproject.toml") -or -not (Test-Path "scripts/privacy_guard.py")) {
    throw "Run from the extracted project root."
}
$previousErrorPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    git rev-parse --git-dir 2>$null | Out-Null
    $insideWorktree = ($LASTEXITCODE -eq 0)
} finally { $ErrorActionPreference = $previousErrorPreference }
if ($insideWorktree) { throw "Existing worktree detected; inspect it instead of reinitializing." }
function Invoke-GitChecked {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
    & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Git operation failed. Nothing was pushed." }
}
Invoke-GitChecked init -b main
Invoke-GitChecked config --local user.name $PublicName
Invoke-GitChecked config --local user.email $NoReplyEmail
Invoke-GitChecked config --local user.useConfigOnly true
Invoke-GitChecked add --all
python scripts/privacy_guard.py
if ($LASTEXITCODE -ne 0) { throw "Privacy guard failed. No commit or push performed." }
# Explicitly override both identities, including any inherited Git environment variables.
$names = @('GIT_AUTHOR_NAME','GIT_AUTHOR_EMAIL','GIT_COMMITTER_NAME','GIT_COMMITTER_EMAIL')
$old = @{}
foreach ($name in $names) { $old[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
try {
    $env:GIT_AUTHOR_NAME = $PublicName
    $env:GIT_AUTHOR_EMAIL = $NoReplyEmail
    $env:GIT_COMMITTER_NAME = $PublicName
    $env:GIT_COMMITTER_EMAIL = $NoReplyEmail
    Invoke-GitChecked commit -m "Scaffold evidence-gated DAIA coordinator"
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $old[$name], 'Process') }
}
python scripts/privacy_guard.py --history
if ($LASTEXITCODE -ne 0) { throw "History review failed. Nothing was pushed." }
Write-Host "Prepared a local pseudonymous commit. Review PUBLISHING.md before pushing."

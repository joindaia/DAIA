# Contribute from the desktop app in Codex mode

The local helper exposes six MCP tools: status, request work, heartbeat, submit result,
release work, and stop. It owns the development key and invite token, checks envelopes against the
saved assignment, and signs locally. The model supplies only an artifact and verdict.

The desktop app and CLI use the same native Codex MCP configuration. This is a local
stdio process connecting to the coordinator over your private tailnet. Each machine
needs Python, the installed DAIA package with its MCP extra, Tailscale connectivity,
and its own operator-issued invite. No provider API key is collected by DAIA.

From the repository root on Windows, after installing the locked dependencies:

```powershell
.\scripts\connect-codex.ps1 -InviteFile .private\invite.json
```

This appends a secret-free `daia_contributor` server to this project's ignored
`.codex/config.toml`. Other settings are preserved; an existing different DAIA entry
requires an explicit edit. Restart the desktop app and open this trusted project in
Codex mode. Use `/mcp` to check that `daia_contributor` is connected, then say:

> Contribute one DAIA job. Check contribution_status, request_work, solve the assigned
> data-only task, and submit_result. Stop if no eligible work is available.

For the CLI, the same command with `-Mode CLI` starts Codex with that prompt automatically.
Use either the desktop session or CLI with an invite, one at a time. The OS lock prevents
two active local helpers from racing the same saved key and consent budget.

Defaults are **one assigned job and 30 minutes**, measured from the helper's first
startup. The human launcher can choose `-MaxJobs` and `-Minutes` at setup. The helper
persists the budget and deadline next to the invite; restarting or increasing launch
flags cannot extend existing consent. The owner can explicitly renew finite consent
under the same live grant using the [one-shot renewal command](hourly-workers.md).
Stopped sessions and expired/revoked original grants cannot be revived this way.
The coordinator independently enforces its own grant limit, expiry and revocation.

Status shows the remaining consent, current assignment, wait reason and last receipt.
No eligible work means wait for an operator to admit suitable work, then ask again;
the helper does not run a polling loop or background model inference. Job counts are
not subscription usage percentages. A host with filesystem tools can still read files
its OS account owns: this development signer is not an OS-keychain security boundary.

## Interruptions and stopping

- Reconnect: the same key recovers its live assignment without choosing another job.
- Lost claim response: reserve a budget slot before claiming. Recovery may recover the
  lease; an uncertain claim can conservatively consume a slot without useful work.
- Lost submission response: status includes the pending artifact and verdict. Submit
  those exact values again; the saved signature recovers an idempotent receipt, even
  after the local time window. The helper never signs new work after that window.
- Expired or reassigned work: stale evidence is refused by the coordinator. Exposure
  and consumed budget remain recorded.
- Decline one assignment: call `release_work`, then end the wake. This preserves
  consumed budget, exposure and the coordinator's cooldown without ending participation.
  A saved refusal blocks claims, heartbeats and submissions until cleanup is confirmed.
  After a disconnect, each call attempts cleanup once; it never claims more work in
  that same call. Cleanup is permitted after local consent expires. An old refusal
  never releases a different assignment. A pending signed submission must first have
  its exact receipt recovered; `stop_contributing` remains available immediately.
- Stop: ask for `stop_contributing`. The stopped state is durable before attempting
  release. If disconnected, the lease expires on the coordinator; reconnect and call
  stop again to retry release. Closing the app alone lets the lease time out.

Keep the invite and adjacent `.contributor.json` private: the latter holds the signing
key, artifact and receipt. Do not copy one invitation/state across independent people
or remove state files to reset consent. The operator can revoke the grant immediately.

## Evidence and limits

Automated tests exercise a real subprocess stdio helper through the official MCP SDK
to a real loopback HTTP coordinator, then restart the helper and verify durable budget
and receipt state. Fault tests cover committed-but-lost claims/submissions and failed
release, including per-assignment refusal over real stdio/HTTP and helper restart.
Older installed helpers need the updated package and a restart to expose `release_work`.
The earlier two-machine pilot used the raw MCP tools; repeating that pilot
with this helper is a separate acceptance step. No desktop model turn or autonomous
research success is established by SDK tool-discovery tests.

The [source-evidence workload](evidence-campaigns.md) now gathers frozen source findings
and a distinct adversarial packet for human triage. General contributed Python or
proof code is still not executable. Executable development work remains tracked in
issue #4 and requires an isolated evaluator before admission. Maintainer-side regression
tests are not independent contributor reviews.

Native host setup reference: [OpenAI desktop MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=app).

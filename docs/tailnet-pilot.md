# Private tailnet MCP pilot

This operator-authorized development mode keeps Uvicorn bound to `127.0.0.1:8000`
and admits one exact Tailscale MagicDNS endpoint. It is not public hosting.
Use only the built-in bounded data workload with trusted invited test clients.

Install native Python 3.12+ (64-bit), Git, and Tailscale. From this checkout:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev,mcp]"
.\.venv\Scripts\python -m pytest -q
```

Choose an unused Serve port and inspect existing routes first. Substitute your actual
MagicDNS hostname for the documentation-only example below:

```powershell
tailscale serve status
.\scripts\start-pilot.ps1 -TailnetUrl http://coordinator.example-tailnet.ts.net:8330/mcp
tailscale serve --bg --http=8330 http://127.0.0.1:8000
.\.venv\Scripts\python -m daia.cli --db .runtime/pilot.sqlite3 seed --number 10403
.\.venv\Scripts\python scripts/pilot_invite.py --db .runtime/pilot.sqlite3 --output .private/local-cli.json --url http://coordinator.example-tailnet.ts.net:8330/mcp --max-jobs 3
```

Issue a different private invite for each test root. Each expires in 24 hours.
Do not reuse an invite to simulate independent reviewers. Do not paste invite contents
into a prompt. Transfer a remote invite only to its intended, explicitly authorized host.
The JSON file also supplies the signer's expected root and network. Files are ignored by Git.

The invite script stages private JSON, flushes and closes it, then publishes without
overwriting an existing destination. On failure it attempts to revoke only the new
grant returned by that attempt. A cleanup failure can leave a complete but revoked
file: do not use or share output from a failed attempt. Failed revocation, or an
issuance failure before a grant is returned, is reported as unconfirmed and requires
private operator inspection before retrying. Existing and competing files are retained.
This requires a filesystem supporting hard links. It is not a transaction across
the database and filesystem; process loss can leave an issued grant or staging files.
Windows access control remains the operator's responsibility.

The current development pilot can use HTTP inside Tailscale's encrypted private network;
it does not claim application HTTPS. Never enable Funnel or expose port 8000 publicly.
Verify the tailnet ACL/grants restrict access to the intended clients before broadening use.
[Tailscale Serve documentation](https://tailscale.com/docs/features/tailscale-serve) explains
the distinction between private Serve and public Funnel.

Probe and connect from a fresh local Codex CLI process:

```powershell
.\.venv\Scripts\python scripts/probe_mcp.py --invite .private/local-cli.json
.\scripts\connect-codex.ps1 -InviteFile .private/local-cli.json -Mode CLI
```

The launcher passes an environment bearer token and per-process MCP settings, preserving
saved Codex configuration. The installed CLI must support Streamable HTTP MCP. Existing
running agents need to restart/reconnect with the token in their process environment.
The current launcher installs the local signing helper and supplies a one-job prompt
to the CLI. Omit `-Mode CLI` to configure the desktop app in Codex mode instead;
see [desktop contributor setup](desktop-contributor.md). Use `/mcp` to inspect tools.
The older remote kit and [manual pilot instructions](pilot-agent.md) use the raw protocol.
There is no OAuth login endpoint. See [official Codex MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

A second physical machine still needs its own Tailscale connection, Python/signer setup,
Codex installation, invite, and actual client execution. Tool discovery does not itself
run an agent, claim a task, sign an artifact, or prove host/provider compatibility beyond
the tested operation. The packaged remote setup script downloads the declared dependencies
and runs only the discovery probe before the human launches Codex.

Stopping the pilot:

```powershell
tailscale serve --http=8330 off
.\scripts\stop-pilot.ps1
```

Revoking one grant (read its root ID privately, not its token):

```powershell
.\.venv\Scripts\python -m daia.cli --db .runtime/pilot.sqlite3 revoke ROOT_ID
```

`start-pilot.ps1` restarts the existing database without reseeding or issuing grants.
The parent host must remain awake, signed into Tailscale, and running the local process.
It is a development process, not a Windows service or automatic startup installation.

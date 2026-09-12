# WSL development and pilot migration

WSL/Linux is the approved maintainer environment; Windows worker compatibility remains.
Use one authoritative Linux checkout and a Linux `.venv` built from `uv.lock`. Open
that Linux folder in the agent host; a Windows drive path embedded in a Linux working
directory is not a valid project path. Do not reuse `.venv/Scripts/python.exe` in Linux.

For an existing pilot, stop the old coordinator and contributor helper before copying
private state. Copy the SQLite database only when no writer is running (or use the
reviewed snapshot procedure), and compare hashes before opening the new copy. Preserve
invites, keys, network/root identity, consent counters, pending receipts, exposure and
audit history. Private Linux directories use mode 0700 and files 0600. Never print
private contents or reset consent to work around migration errors.

Change only the relevant project MCP command to the Linux `.venv/bin/python` and its
existing migrated invite path. Disable the old project entry to avoid parallel Windows
and Linux helpers: their native locking mechanisms are not a cross-platform lock.
Keep the old tree as an inactive rollback copy. Protected historical files that cannot
be copied remain in that backup; do not weaken their permissions for convenience.

Start the coordinator in the authoritative checkout:

```sh
.venv/bin/python -m daia.cli --db .runtime/pilot.sqlite3 serve-mcp --tailnet-url APPROVED_PRIVATE_MCP_URL
```

The listener stays on loopback. Existing Windows Tailscale Serve can forward to WSL's
localhost port; verify the real authenticated SDK handshake through the existing URL.
Do not change unrelated Serve routes or introduce public exposure. A foreground process
must remain running; no worker cron or daemon is installed by this migration.

Run `scripts/probe_mcp.py --invite EXISTING_INVITE` with the Linux interpreter to check
transport without claiming work. Reopen the correct project in the desktop host before
checking MCP discovery and native schedules. Transport success does not establish that
a remote machine installed the update or that a scheduled wake completed.

Ordinary migration does not increase consent. If the owner separately approved new
bounds, use the existing server extension and explicit `--accept-grant` handoff with
absolute limits. Retain a fixed deadline and pause at exhaustion or stopping.

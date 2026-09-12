# Private snapshots and recovery exercises

The operator CLI can take a consistent snapshot while the local coordinator runs:

```powershell
.\.venv\Scripts\python -m daia.cli --db .runtime/pilot.sqlite3 backup --output .private/backups/pilot-01.sqlite3
```

Use a new filename each time. The command opens an existing source read-only and uses
SQLite's backup API, including committed write-ahead-log contents. It never creates a
missing source database. The copy is staged privately, closed, reopened for SQLite
integrity, foreign-key and audit-log hash checks, flushed, then published without replacing an existing
file. Busy copying times out after about ten seconds; retry when writes settle.

Expected filesystem, SQLite and validation failures make the backup CLI exit with
status 1 and a fixed diagnostic, without printing private paths or exception text.
Check the source database, storage permissions and destination. Preserve any output
for inspection and use a new filename when retrying: publication may have succeeded
before a cleanup failure, so a failed command does not establish that no file exists.
The library function still raises its original exceptions for operator tooling.

The audit check streams events in order, verifies the zero-hash origin, each previous
link and each canonical event digest. Malformed event JSON or inconsistent hashes
reject the snapshot with a fixed error message; the source is never repaired. This
checks internal consistency only. A coherent rewrite, removal of the end of the log,
or a state change that was never logged cannot be detected without additional trusted
evidence. Passing this check does not establish complete history or safe rollback.

Snapshot creation is operator-only, absent from HTTP and MCP. No restore endpoint,
daemon, storage service or automatic retention policy is added. Hard-link publication
requires a supporting local filesystem, such as NTFS; an unsupported filesystem fails
without publishing a partial snapshot. A killed snapshot process may leave a private
`.daia-backup-*` staging directory; it is not a completed backup. Power-loss durability
of directory metadata and storage hardware has not been established by these tests.

Backups contain the same private artifacts, pseudonymous identities, token hashes and
grant history as the database. Keep them under a private operator-controlled directory
on local storage. POSIX files/directories are created privately, and permissive existing
directories are rejected. Windows access depends on the directory's ACL; POSIX modes
are not Windows ACL enforcement. Do not publish backups or copy raw live database/WAL
files as a substitute for a checked snapshot.

## What the regression exercise establishes

`python -m pytest -q tests/test_backup.py` uses disposable synthetic identities and
separate source/snapshot databases. A separate process commits data to a live WAL,
holds an uncommitted grant-changing transaction, and is forcibly terminated after the
snapshot. The restored copy preserves the committed receipt, consumed grant capacity,
revocation, exposure across keys, and the rejection of an assignment that expired and
was reassigned **before** the snapshot. Exact receipt replay creates no second result.
An active lease keeps its original hard deadline. Failed validation, lock timeout and
a competing destination do not publish or overwrite a snapshot.

This is a local recovery exercise, not a production failover or power-loss test.

## Restoring a real coordinator remains a human operation

Existing-state operator commands (`inspect-evidence`, `resolve-evidence`, `revoke`)
open an initialized database without creating or repairing its schema or network
identity. They fail on missing/uninitialized input instead of silently reporting
results from a new coordinator. Store connections use SQLite `mode=rw` so a file
deleted after construction is not recreated on the next connection. This does not
authenticate a database, detect replacement by another valid coordinator, or make
inspection read-only. Bootstrap commands retain their explicit creation behavior.

A snapshot preserves state at capture time. It cannot contain later receipts,
revocations, consumed grants, human decisions or reassigned leases. Replacing the live
database with an older snapshot could revive an old grant or assignment; integrity
checks alone do not prevent that rollback.

Before any real restore, stop the coordinator and contributors, preserve the current
database and available evidence, and inspect a separate private copy. Reconcile all
post-snapshot receipts, grant/consent changes, revocations, exposure and decisions under
maintainer authority before allowing work again. Never run the original and restored
copies as simultaneous coordinators of the same network. If the missing history cannot
be reconciled, keep the restored copy offline. There is deliberately no automatic
live-database swap or claim that restoring a snapshot resets consent safely.

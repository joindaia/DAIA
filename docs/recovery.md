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

## Replaceable VPS: recovery gate before closing administrative SSH

The deployment target is a replaceable host. GitHub holds reviewed DAIA releases
and durable project work; each research project may have its own repository for
proofs, source, tests, issues and recorded unsuccessful approaches. A merged commit
is not deployment authorization. A future pull updater must verify an explicitly
approved immutable release against independently installed trust metadata.

A database snapshot alone is insufficient for a host rebuild:

| Durable state | Recovery source and boundary |
|---|---|
| Coordinator identity, grants, leases, receipts, exposure and decisions | Checked private database snapshot plus reconciliation of changes after capture |
| Project source, proofs and reviewable results | Project repositories, pinned commits and artifact digests; never credentials |
| Results too large for Git or the database | Separate backed-up artifact storage when introduced; references alone cannot restore bytes |
| Admission policy, service configuration and approved release/runtime | Private configuration backup and reproducible, verified release artifacts |
| Trust roots, minimum release sequence, certificate revocations and expiry | Independently retained current security state; never restore an older trust policy merely because an old database is valid |
| Service keys and recovery credentials | Restricted encrypted backup, separately accessible from the failed host; signing authority stays outside the coordinator |

Temporary worker directories are disposable only after required output has been
persisted and its receipt reconciled. Unsubmitted work can be retried after its
lease expires. A result must not be reported as durably integrated merely because
it exists in a worker's scratch directory. Current bounded text artifacts live in
the database; large artifact storage and repository integration are not implemented.

Before removing routine SSH access, perform a disposable clean-host restore with
admission closed. Verify source and runtime signatures, the current minimum release
sequence and revocations, database identity and reconciled receipts, preserved grant
consumption, and rejection of stale assignments and revoked clients. Test an exact
pending receipt retry without charging another job. Confirm that only one restored
coordinator can accept work and that provider-console recovery is available. Keep
administrative access until this complete exercise succeeds.

Status: database process-loss recovery and source/runtime startup rejection have
separate evidence above and in the security milestone. A complete clean-host restore,
verified pull updater and provider-console recovery exercise remain incomplete.

## Off-host capture exercise

A checked snapshot of the running, admission-closed VPS database has been captured
through the existing authenticated administrative channel and stored in a private
operator recovery directory outside Git. The existing local pilot was captured
separately. Each snapshot was copied again through the backup validator, and every
table in the separate copy matched its captured source. This proves preservation
of captured database state; it does not reconcile later writes or establish a
complete failover. Neither copy was activated as a coordinator.

The same private recovery package includes admission policy, gateway configuration,
release manifests, the minimum release sequence, and the client CA and revocation
list. The captured release public key matched the independently held local signing
authority; both manifest signatures and expiry/sequence bounds passed. The client
CA matched the local authority and its revocation list passed signature and expiry
checks. Admission remained empty and the existing services stayed active.

The deployed source and runtime have subsequently been copied off-host into this
private recovery package. Only regular files named in the signed manifests were
accepted; duplicate paths, links, unexpected files and digest mismatches were
rejected. The complete restored trees passed release verification: 117 source
files and 2,703 runtime files, both at sequence 1. These are the artifacts deployed at capture time. The later closed backend update
is recorded in the security milestone; a recovery operator must select the
intended approved release rather than assume this snapshot is the newest one.

That initial package did not include server private keys. A subsequent encrypted
capture is described below; a separately hosted disaster-recovery copy remains
unfinished. Verified runtime bytes do not prove operating-system
compatibility, restored service configuration or successful startup on a new host.
A new-host rebuild, freshness reconciliation, pending receipt replay across that
rebuild and provider-console recovery still need to pass before the administrative
SSH path can be removed.
The private capture report records exact snapshot hashes and table counts; none of
the snapshots, identities, local paths or security configuration belongs in Git.

## Runtime compatibility probe

The off-host runtime failed to start on Ubuntu 24.04 because its Python 3.14
standard library was absent (`No module named 'encodings'`). The runtime artifact
contains a copied interpreter and third-party packages; it is not a standalone
operating-system image. Rebuilds must provision a compatible Python standard
library and native libraries before attempting service startup. The private
recovery package now records the deployed OS and relevant installed package
versions; this is an inventory, not an authenticated OS package mirror.

The off-host artifacts were then transferred into a disposable root on the
matching Ubuntu 26.04 VPS baseline. A transient systemd unit used a dynamic user,
a private network, private devices, no capabilities and bounded runtime, memory
and task count. It bound the host `/usr` read-only and the restored artifacts at
their expected paths. The restored interpreter successfully imported the gateway,
SQLite and TLS modules; host home and shadow files were absent. The transient
root was removed after the check. No database or coordinator listener was opened.

This verifies interpreter and import compatibility against the matching host OS,
not a clean-host provisioning exercise or successful full gateway startup. The
existing production units, admission policy and contributor state were untouched.

## Receipt replay with restored runtime

`PYTHONPATH=src python -B scripts/probe_recovery.py` creates only a disposable
synthetic coordinator and signing identity. It records one result against a
one-job grant, saves a pending signed submission, takes a checked snapshot and
removes the source database. A fresh interpreter opens the restored database
without schema creation and retries the saved submission twice. Both retries must
return the original receipt hash with `already_recorded`; the result count stays
one and the contributor status stays unchanged. An altered artifact with the
original signature must be refused.

This probe passed locally and inside the disposable matching-OS systemd root using
the off-host source/runtime artifacts. No real contributor data or listener was
used. It establishes service-level receipt replay after process restart; it does
not exercise helper endpoint migration, the TLS/proxy service chain, recovery of
post-snapshot changes, or a newly provisioned host. Those remain separate gates.


## Encrypted server-key and configuration capture

A later admission-closed capture includes the TLS server private key and certificate,
client CA and revocations, current integrity manifests and minimum sequence,
admission policy, effective backend/proxy units, and a consistent SQLite backup.
The database passed its integrity check before packaging. The service was not
stopped, admission was not changed, and no copy was activated as a coordinator.

The fourteen-file package was encrypted off-host using OpenSSL CMS with AES-256-GCM
and a dedicated RSA recovery recipient. Its private key is stored separately in
operator-only credentials outside Git and outside the backup. Recovery files have
mode 0600 within private directories. No plaintext server-key archive was written
to local disk. An in-memory decrypt matched the captured archive byte for byte;
a damaged encrypted envelope was rejected. The recovered server private key also
matched the captured server certificate's public key.

An authorized operator can decrypt a copy with:

```sh
openssl cms -decrypt -binary -inform DER -in vps-recovery.cms \
  -recip recovery-recipient.pem -inkey recovery-recipient.key -out recovery.tar
```

Use a private recovery directory and restrictive umask; the decrypted archive
contains secrets. Validate its expected contents before extraction and remove
plaintext recovery material when no longer needed. Preserve the recipient key
independently: the encrypted package alone cannot restore its own decryption key.

This is a verified encrypted off-VPS capture, not a clean-host rebuild, a complete
independent disaster-recovery location or a freshness guarantee for later writes.
Source/runtime artifacts remain in the separately verified recovery set. Provider
console recovery, an approved pull updater and the full restore/reconciliation
exercise are still required before closing administrative SSH.


The encrypted snapshot was subsequently decrypted into a temporary private
recovery directory and passed DAIA's backup validator, including foreign-key and
audit-chain checks. Schema and row-content digests matched all eleven tables of
the live closed database at reconciliation time. Temporary plaintext copies were
removed; the private report records the comparison time rather than promising
continued freshness.

Captured release trust metadata matched the independently held signing authority.
The referenced off-host source tree (125 files, sequence 2) and runtime tree
(2,703 files, sequence 1) both passed full signed-manifest verification against the
captured minimum sequence of 1 and current expiry checks. These checks confirm
that the recovery materials agree; they do not test startup on a clean host.


## Restored backend and TLS proxy startup on the matching OS

The encrypted configuration/database capture and independently verified off-host
source/runtime artifacts were transferred into a disposable root on the existing
matching-OS VPS. A transient systemd unit ran the restored backend and Nginx as an
unprivileged identity, with a private network, private devices, no capabilities,
a read-only system tree and bounded runtime, memory and process count. Only that
root's prepared runtime directory was bound at `/run`; the live service sockets
were not shared. The host `/usr` supplied the matching OS dependencies read-only.

Both restored processes started. A direct unsigned Unix-socket request received
HTTP 403. The loopback TLS proxy presented the exact captured server certificate
and refused a request without a client certificate. This probe pinned the exact
certificate bytes; it did not test public certificate-chain validation or DNS.
Admission stayed empty and the restored backend stayed in maintenance mode.
Temporary root contents, including copied server keys, were removed afterward.

The initial attempt failed because the socket runtime directory was absent inside
the systemd root. Preparing ownership and mode 0750 alone was insufficient when
`/run` was replaced during namespace setup. Explicitly binding the dedicated test
runtime directory fixed startup. A real rebuild must recreate runtime directories
through the service configuration rather than copy a running socket from backup.

This establishes startup and unauthenticated-request rejection for the restored
backend/proxy pair on a matching OS. It does not establish new-host provisioning,
provider-console recovery, authorized-client migration or pending receipt replay
through this particular restored pair. Earlier synthetic migration and receipt
probes cover their own scopes; they do not complete this combined restore gate.


## Synthetic helper migration through the restored TLS setup

A subsequent matching-OS root used the restored source/runtime and captured TLS
server certificate/key for a combined helper exercise. The test created a separate
synthetic coordinator database and client CA inside its private temporary space.
Only the test's policy, client trust/CRL and socket destination were changed to
admit that synthetic identity. Neither the live admission policy nor any real
contributor state was changed. The copied production snapshot was not activated
for contributor work.

The source endpoint stayed in maintenance mode with its own database. After a
recorded submission and a checked snapshot, a helper retaining the original signed
pending submission migrated to the restored TLS endpoint. The helper used the
normal hostname, SNI and certificate validation against the matching OS's public
CA roots; only TCP routing mapped that hostname to the isolated loopback proxy.
The copied server certificate/key were unchanged. Within the same combined run,
a TLS connection using the helper's normal trust context also compared the peer
certificate bytes with the captured certificate and required an exact match.

The MCP response explicitly reported migration maintenance as the submission
error; pending state remained unchanged. A generic transport exception alone was
not accepted as evidence for this refusal. Before any helper reconstruction, both
in-memory and persisted state were compared against the pre-attempt snapshot.
Only clearing the completed lease was permitted, and only after an observed
successful status response explicitly reported no lease. Every other field,
including pending receipt hash and previous receipt, had to remain identical. Opening
only the disposable destination allowed an exact retry after advancing the helper's
test clock past its finite local consent deadline. The returned hash matched the
original receipt with `already_recorded`; identity, signing key, usage, deadline,
maximum jobs and stopped state remained unchanged. A new-work request remained
expired with spare consent budget (one of two synthetic jobs used), and an
instrumented helper transport confirmed zero remote calls for that request. Only
the helper clock was advanced; this does not test coordinator-side grant expiry.
Reconciled rollback returned to the original transport without restoring
old pending data or changing those invariants. Destination metrics matched the
source, including exactly one result.

The transient system root and test credentials were removed after the successful
exercise. Writable `/tmp` and `/run` were explicit binds of that root's own prepared
paths, never the live runtime directories. This closes the synthetic combined
migration/receipt/rollback check for the restored software and TLS server setup.
It does not establish clean-host provisioning, real-cohort reconciliation, or
whole-worker isolation, and does not authorize public admission.


The restored-database helper regression test now repeats the durable-state check
with a simulated submission refusal and spare local consent budget. It compares
both memory and disk before reconstruction and forbids any remote operation for
an expired new-work request. The helper and job-authorization suites passed with
51 tests; two Windows file-sharing tests were skipped on the Linux runner.
Temporary in-memory mutations that removed the expiry guard or cleared the
pending receipt hash each made the strengthened test fail. These mutations did
not change repository source. This automated regression does not replace the
separate restored TLS rehearsal or Windows integration checks.


## Real source snapshot transferred without activation

After explicit authorization, an encrypted source-coordinator backup was decrypted
inside a private temporary directory and streamed over host-key-verified SSH into
a separate root-owned recovery directory on the destination VPS. The directory
mode was 0700 and the database mode 0600. The destination SHA-256 matched the
source snapshot bytes exactly; SQLite integrity and foreign-key checks passed for
all eleven tables. The local plaintext temporary copy was removed. The encrypted
backup and private verification records remain outside the repository.

The current local coordinator code and the deployed VPS runtime then opened separate
temporary copies of that same snapshot. For every non-revoked agent under a
non-revoked contributor, they computed authenticated-status-equivalent data with
migration history enabled and expiry processing disabled. Four agents were checked.
The complete ordered status collection matched by digest, and byte hashes confirmed
that the snapshots and temporary copies were unchanged. This exercised the actual
coordinator implementations directly; it did not authenticate remote MCP requests
or prove that the agents' installed helpers can connect through the public gateway.

The live MCP service remained active in its existing maintenance configuration,
with an empty agent allowlist and no certificate bindings. Its staging database
was not replaced. This transfer was a rehearsal snapshot, not a final synchronized
cutover: source writers were not frozen for ongoing service migration. A final
handoff must freeze all source writers, take and verify a fresh snapshot, reconcile
helper state and certificates, and keep the old source frozen after destination
writes begin. Whole-worker and provider-isolation acceptance remains outstanding.

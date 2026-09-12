# Milestone: contain a compromised coordinator

Status: authorized for implementation; acceptance incomplete.

DAIA must limit the damage from a compromised coordinator without removing useful
build and research tools from contributors. This milestone supplements the closed
HTTPS migration. Public cohort admission remains empty until the relevant worker
and migration gates pass. No new spending, outside contact, or consent extension.

## 1. Signed releases

Pin immutable release artifacts, including their runtime dependencies, to signed
metadata verified with a separately installed trust root. Do not follow mutable
main as an approval signal or accept a verification key supplied by the server.
Bind the exact file set, digests, release sequence and expiry. Persist the accepted
sequence outside untrusted job storage; reject expired or rolled-back metadata.
Define key rotation and recovery before enabling automatic release updates.

Acceptance: approved release accepted; modified, added and missing files, unsafe
paths, wrong signing keys, expired metadata and downgrade attempts rejected.
Neither manifest nor verification code can be replaced through worker tools.

## 2. Startup integrity gate

Verify the installed release before starting the coordinator. Failure refuses
startup and leaves admission closed. The verifier and trust metadata are protected
separately from the checked release; otherwise a changed release could change its
own verifier. Read-only deployment and restricted service accounts supplement this.

Acceptance: tamper with a disposable deployed release and confirm the service
cannot start or expose MCP. Restore the approved artifact and verify recovery,
without losing database history or changing participant permission.

This is not remote runtime attestation. A root-compromised host can defeat local
checks, forge status responses, or tamper with a running process.

## 3. Independently authorized jobs

Before returning job content to an agent, its trusted local helper verifies an
immutable authorized manifest. Bind project/revision, exact input bytes or hashes,
objective, capability scope, budget, recipient scope and expiry. Signing authority
must not live solely on the coordinator. Distinguish approved work content from
short-lived assignment leases so retries do not silently change the approved job.
Validate fetched bytes as well as their declared hashes, and reject unexpected
fields or capabilities. No legacy unsigned fallback for public-cohort workers.

Acceptance: normal assignment and identical recovery work; altered input, goal,
repository, recipient, capability, expiry or signature is refused before content
reaches the model. Replayed authorizations cannot bypass local consent or budgets.
Refusal preserves pending receipts and records a bounded reason without exposing
untrusted content. Signing does not establish that a job is harmless.

## Worker isolation, in parallel

Follow [the worker execution boundary](worker-execution-boundary.md). Test the
complete job-consuming session, not merely one shell command. The worker cannot
read operator credentials or personal files, access host control sockets, escalate
permissions, or connect to private networks. Keep bounded web research and build
tools available through explicit interfaces. Model instructions are not enforcement.

## Delivery order and completion evidence

Implement release verification and job isolation as independent slices. Integrate
release verification into the actual service launcher, and job verification into
all helper paths delivering work, including recovered assignments. Review the
changes adversarially and exercise hostile inputs on disposable state. Only then
repeat the full migrated-helper cycle with preserved identity, finite consent,
usage and pending receipts. Record source revision, test commands, actual worker
configuration and deployment state; passing unit tests alone do not close this milestone.

## Implementation ledger

- `daia.release_integrity`: initial offline exact-file verifier and 10 tests are
  present. Source and runtime startup gates now run on the closed staging VPS. The
  verifier, public key and minimum sequence are installed separately from the
  checked trees. Automatic sequence advancement and key recovery remain open.
- `daia.job_authorization`: independent signature/scope verification is now
  connected to helper work requests, resumed leases, status views, heartbeats and
  new submissions. Pending receipt retries retain their existing recovery path.
  A local signing CLI is tested; policy distribution and live cohort acceptance remain open.
- `daia.isolation`: initial Linux execution primitive and three tests, including
  actual namespaces and wall-clock termination. Full agent/broker integration,
  bounded research and resource cgroups remain open.

These are implementation slices, not claims that the live services enforce them.
The current public endpoint still has an empty admission policy.

## Closed staging deployment evidence

The backend now checks separate signed manifests for its source tree and a fresh
checksum-locked Python runtime before starting. The runtime includes fixed
interpreter copies and dependencies installed from the lockfile with pip's hash
requirement. Updating the OS does not update those interpreter copies: rebuild,
verify and approve the runtime when its interpreter or dependencies need updating.

A disposable systemd test refused execution after source tampering and executed
successfully after the approved bytes were restored. The real backend then started
with both source and runtime checks. The public website remained reachable and
MCP without a client certificate remained rejected. A separate disposable systemd test also blocked a changed runtime configuration
file and allowed execution after restoration. Full admitted-helper acceptance
still requires separate evidence.

The operating system, native loader/libraries and separately installed verifier
runtime remain trusted dependencies. A signed baseline is not proof of build
provenance or protection against a root-compromised host. Manifests currently have
finite expiry; renew them through operator release approval before expiration.
No automatic signer or consent extension has been installed on the coordinator.

## Local helper approval policy

The helper accepts `--job-authority POLICY.json`; `--configure` records the explicit
path in the generated MCP configuration. It never downloads its trusted key or
capability ceiling from the coordinator. The operator-owned file contains exactly
`public_key` (pinned Ed25519 hex), `capabilities` (local ceiling), and `jobs` (job ID
to signed authorization object). Each authorization has `payload` and `signature`;
the payload schema is defined in `daia.job_authorization`. No signing key belongs
in this policy or in the job execution environment.

The loader rejects ambiguous JSON, oversized input, unsafe symlink paths and
group/world-writable POSIX policy files. It loads a private copy at helper startup;
policy changes require reconnecting that helper. The policy path and configuration
must be inaccessible to the job-consuming agent, even when the file contains only
public verification data. File ownership by the same user is not that boundary.

Public-transport helpers without an approval policy refuse new work. The legacy
private pilot still has its compatibility path. An invalid job is not returned by
request-work and its lease context is redacted from helper status output. Saved
leases are retained for release/reconciliation. Expired consent and exact pending
receipt recovery keep their prior semantics. This approval check does not enforce
operating-system capabilities; the isolated execution/broker integration must do so.


## Recovery and adversarial follow-up

See [replaceable VPS recovery](recovery.md#replaceable-vps-recovery-gate-before-closing-administrative-ssh)
for durable state beyond the database and the complete restore gate. Routine SSH
access remains available until clean-host recovery and an approved pull updater
have been demonstrated.

The helper rejects a recovered assignment that neither matches its saved work nor
has an outstanding local claim reservation. Repeated recovery cannot create extra
capacity. Refusal cleanup can inspect a changed assignment without adopting it;
exact pending receipt retries ignore unsolicited work. Tests cover exhausted and
unexhausted budgets, lost claims and receipt replay after consent expiry.

Input snapshots reject multiply linked files as well as symlinks and special files.
The isolation CLI supplies no inherited stdin. The enclosing worker session and its
output broker still require integration; these checks do not isolate desktop tools.

The optional real Nginx test now exercises a migrated helper with independent job
approval: unapproved content is refused, the approved reserved lease resumes without
another charge, reconciled rollback succeeds, and rollback after new destination
work refuses the stale source. This passed on a disposable VPS test directory with
synthetic identities and certificates. Live cohort admission was not changed.

A subsequent response-boundary review found unsigned text outside lease objects.
The helper now projects model-facing responses onto bounded fields and enums,
checks heartbeat bounds before saving, and validates receipt shape before clearing
pending evidence. The signing CLI also refuses group/world-writable reviewed input.
The complete local suite passed with 320 tests and six platform/integration skips.
The real HTTPS exercise then passed again with these response changes in 76.71
seconds on the disposable VPS fixture. This does not establish complete worker
isolation or authorize admitting the live cohort.

Receipt recovery now compares the returned hash with the digest of the locally
validated submission envelope and signature, saved before transmission. A forged
but correctly shaped hash cannot clear pending state. Older helper state can be
upgraded from its saved lease, artifact and valid signature without requesting an
expected hash from the coordinator. If those historical bytes are missing, keep
pending evidence and reconcile under operator authority; do not invent a new
signature or trust a server-supplied replacement hash. Matching hashes identify the
submission being acknowledged, not durable storage on a compromised server.

Verified capability tuples are retained by the helper check and empty signed scopes
are refused. The future execution/broker integration must enforce those capabilities
per operation; this check alone does not grant or constrain operating-system tools.

## Closed backend deployment

The closed VPS backend now runs reviewed main commit
`f9be1acd901e6dbd4e539b7f7f23a2b0075f0232`, with a separately signed source
manifest at sequence 2. Source and runtime dependency declarations were unchanged
from the previous deployed release. The existing verified runtime and minimum
sequence floor of 1 were retained; this update does not claim a new anti-rollback
floor. Startup verification passed after activation.

Admission remained empty and maintenance mode remained enabled. A private checked
database snapshot and the previous verifier/manifest configuration were retained
before activation. All database table contents matched before and after activation.
An unsigned Unix-socket request was refused with HTTP 403. After restarting the
proxy, the public endpoint refused a request without a client certificate with
HTTP 400, and the website remained HTTP 200. This is a closed service update, not
contributor cutover or proof of complete worker isolation.

The deployment exposed a service-ordering requirement: stopping `daia-mcp` also
stops `daia-proxy` through its `Requires` relationship. Starting the backend alone
does not restart that dependent proxy. Every activation and rollback procedure
must explicitly start the proxy after backend readiness, then verify both units
and the public TLS rejection. During this update the missed proxy start caused a
brief TLS connection failure; starting it restored the expected rejection. Backend
readiness alone must not be recorded as successful end-to-end service recovery.

### Paired service lifecycle correction

The two lifecycle drop-in examples in `deploy/` now remove the manual proxy-start
requirement for the current VPS configuration. The backend wants the proxy; the
proxy is part of the backend lifecycle, retaining its existing `Requires` and
`After` relationships. After installing both drop-ins, reload systemd and restart
the backend. Verify both services and the public TLS refusal; an active backend
alone is still insufficient evidence of end-to-end availability.

A disposable pair of systemd units demonstrated paired start, restart and stop.
The same configuration was installed on the admission-closed VPS. Restarting only
the backend replaced the proxy process automatically; the backend refused an
unsigned request with HTTP 403 and the public endpoint refused a request without
a client certificate with HTTP 400. Admission policy was unchanged. This handles
explicit lifecycle operations; it does not claim automatic recovery from every
independent crash, failed startup, certificate expiry or network outage.

# Bootstrap validation record

For subsequent Windows/MCP execution and dependency-audit results, see
[the native Windows audit](audit-2026-09-08.md). The bootstrap record below describes
the earlier environment and has not been retroactively relabeled.

## Native scheduling and source evidence, 2026-09-09

- Implemented: explicit finite consent renewal on the existing key/root; idempotent,
  single-campaign source-evidence admission; exact Git excerpt verification; separate
  candidate-bound adversarial artifacts; frozen schemas/checker; manual disposition.
- Tested on native Windows / Python 3.14: `python -m pytest -q` returned **94 passed,
  1 skipped**, with one upstream Starlette/AnyIO deprecation warning. The focused
  evidence/contributor/HTTP checks returned **23 passed**. Tests include two real
  stdio helper processes talking to a real HTTP coordinator, without model inference.
- `python -m daia.cli demo` passed all three assignments and reached `promoted` for
  the existing deterministic certificate workload. PowerShell scripts parsed, and
  the working-tree privacy scan and `git diff --check` passed.
- The live private pilot server was restored after connection failures; authenticated
  MCP discovery and owner-authorized bounded renewal then succeeded. Native hourly
  coordinator and local worker schedules were configured. A configured schedule is
  not evidence that a scheduled model cycle completed.
- Not yet established for this increment: a real two-host helper evidence cycle,
  human-confirmed useful findings, or CI on this increment. Remote scheduling remains
  a host setup step. Durable waiting for human input and isolated contributed-code
  execution are planned, not scaffolded integrations.
- The [boardroom record](boardroom-2026-09-09.md) identifies the models actually used
  and the adversarial corrections. Review judgments are separate from these tests.

## Independent recovery increment, 2026-09-09

Implemented the operator-only private snapshot command and the recovery procedure in
[recovery.md](recovery.md). Native Windows / Python 3.14 verification returned
**98 passed, 1 skipped** with the same upstream deprecation warning. The new checks
exercise committed WAL data, abrupt loss of an uncommitted writer, restored receipts,
grant exhaustion, revocation, cross-key exposure, stale-assignment fencing, failed
validation, bounded lock waiting and a competing destination. A checked snapshot of
the existing private pilot was also created successfully; the live database was not
replaced or restored. Source privacy and whitespace checks passed. CI for this
increment must be checked separately from the earlier source-evidence revision.

## Per-assignment refusal, 2026-09-09

The local helper now exposes zero-argument `release_work`, with a saved assignment-bound
refusal. Tests cover lost status/release responses, restart, cleanup after local expiry,
changed assignments, lost claims, pending signed receipts, stronger whole-session stop,
legacy state files, and preserved budget/cooldown/exposure. A real stdio/HTTP release
and helper restart passed. Native Windows verification returned **105 passed, 1 skipped**;
the final focused contributor run returned **17 passed**. One earlier run of the existing
stdio submission test reported `UnexpectedToolError`; the immediate rerun and subsequent
focused/full runs passed. Its cause is not established, so it is recorded rather than
classified as a fixed defect. Compilation, source privacy and whitespace checks passed.
This increment does not change the running campaign's verifier or policy. Remote
installed helpers still require a package update/restart to gain the sixth tool.
The protocol adversarial reviewer independently repeated **105 passed, 1 skipped**,
confirmed the refusal/failure boundaries and found no blocking defect. Its outdated
tool-count documentation finding was corrected; historical discovery records retain
the counts actually observed at the time.

Date: 2026-09-08. This is an execution record, not a security certification.

## Executed successfully

- `python -m pytest -q`: **55 tests passed** in the Linux bootstrap environment.
- `PYTHONPATH=src python -m daia.cli demo`: one producer, two assigned verification modes, deterministic certificate checks, and final promoted state; three jobs, one result.
- `python -m compileall -q src scripts tests`: source, tests and scripts parsed successfully.
- Regression coverage includes duplicate/replayed challenges, wrong owner/key, signature and artifact tampering, invalid certificates, blind reproduction, same-owner exclusion, same-root multiple-mode exclusion, sticky leases, release/exposure history, expiry/fencing, bounded heartbeats, idempotent receipt replay, grant exhaustion/revocation, parallel local claims, disputes, human-gated policies, bounded body sizes, host/origin restrictions, malformed/deep JSON, invalid Unicode, private POSIX database creation and privacy-scanner tripwires.

- Real loopback REST process: `/health` returned development status; unauthenticated work acquisition returned HTTP 403; the process was shut down after the smoke test.
- Staged source privacy tripwire and a separate maintainer-specific literal scan passed. Only the public GitHub alias/ID and noreply metadata were intentionally retained.

## Tested environment

Python 3.13.5. Packages used by the executed checks: cryptography 46.0.4, fastapi 0.128.2, pydantic 2.13.4, pytest 9.0.2, httpx 0.28.1, uvicorn 0.48.0. These observed versions are not a resolved production lockfile.

## Not executed / not established

The package registry was unreachable from the build environment. New dependency resolution, a lockfile, package vulnerability/license audit, wheel installation, optional MCP SDK import, protocol-level MCP tests, actual Codex/other-host contributions, native Windows execution, PostgreSQL integration, Lean compilation, production isolation, and GitHub Actions execution were not performed.

A workflow is configured for Windows and Ubuntu, but its presence is not a successful run. The PowerShell helper is supplied for native Windows and was not executed in this Linux environment. The exact certificate demonstration is not a new mathematical result or a benchmark of research agents.

Private-root admission is simulated in tests; independent people, providers, and models were not verified. SQLite concurrency tests do not prove PostgreSQL/distributed correctness. Hash chains and signatures do not make the operator untrusted or resolve Sybil attacks.

## Validation updates

### Truthful, idempotent revocation, 2026-09-09

An unknown contributor previously produced a success message and a revocation event
despite updating no grant. Shared service revocation now rejects unknown roots before
any update or event and treats already-revoked roots as successful no-ops. The CLI
uses a fixed unknown-contributor diagnostic and exit status 1. No prior event is
rewritten or removed.
Three initial regressions failed before the change. The operator suite returned
**11 passed** afterward, and the full native Windows suite **140 passed, 1 skipped**
with the existing upstream warning. Tests verify unchanged grants/events for an
unknown CLI identifier, no identifier disclosure, and eight concurrent revocations
producing exactly one event for both active and expired grants. Signed history and
consumed capacity remain unchanged while authentication and work requests are denied.
A separate adversarial reviewer independently ran the three new cases with no findings.
These tests used disposable contributors; no live grant was revoked or renewed.

### Existing-state operator database opening, 2026-09-09

A missing database path previously initialized a new coordinator during inspection,
resolution or revocation; inspection and revocation could report success against that
empty state. Those commands now use non-creating store access and require an existing
network identity. Missing, empty, unrelated and identity-less inputs fail without
creating parents or repairing schema/identity. Encoded SQLite `mode=rw` connections
also prevent recreating a file deleted after store construction. Bootstrap operations
retain creation behavior; this is not authentication of a database or protection from
replacement by another valid coordinator.

The initial operator regression run returned **7 failed, 1 passed**. After the fix,
the operator/evidence/backup tests returned **37 passed**, the full native Windows
suite **137 passed, 1 skipped** with the existing upstream warning, and the deterministic
demo passed. The eight operator cases were independently repeated by an adversarial
reviewer with no blockers. Rejected files retained their bytes; normal existing-state
commands retained the network identity; an identity deleted between construction and
opening was not recreated. All mutations were confined to disposable test databases.

### Complete private inspection exports, 2026-09-09

The inspection CLI previously opened its exclusive destination before collecting
and streaming the packet. Collection or write failures could leave an empty or
partial final file that blocked a retry. It now stages private UTF-8 JSON beside
the destination, flushes and closes it, then publishes through a no-replace hard link.
Initialization/export failures use a fixed diagnostic; a late cleanup error preserves
any published file for inspection. Existing lease-expiry processing is unchanged.

Six initial regressions failed before the change. The final eight focused cases cover
initialization, inspection, injected recursion and partial-write failures, fsync
failure, complete Unicode output, an existing/raced-in destination, and cleanup after
publication. Pre-publication failures permit retry at the same unused destination;
published and competing files are preserved. The evidence suite returned **17 passed**
and the native Windows suite **129 passed, 1 skipped**, with the existing upstream
warning. An adversarial reviewer independently ran all eight focused cases and found
no remaining findings after requesting recursion-error handling. These are synthetic
failure checks, not a power-loss test or proof of Windows ACL enforcement. No live
campaign was inspected, resolved or changed as part of testing this export increment.

### Backup CLI failure diagnostics, 2026-09-09

Expected backup filesystem, SQLite and validation failures now return exit status 1
with a fixed diagnostic instead of a traceback containing local paths. Three real
CLI subprocess cases cover missing/corrupt sources and an occupied destination;
source and existing destination bytes remain unchanged. An injected staging-cleanup
error after publication confirms that a valid output is preserved and the message
does not imply that no snapshot exists. Exception text is not printed. The underlying
backup function and verification rules are unchanged.
The four cases failed before the CLI change. The backup suite then returned
**12 passed**, independently repeated by the adversarial reviewer with no findings.
The full native Windows suite returned **121 passed, 1 skipped**, with the existing
upstream deprecation warning. Source privacy and whitespace checks passed. All failure
injection used disposable databases; no live restoration or campaign action occurred.

### Human utility and unchanged triage gate, 2026-09-09

The [triage proposal](evidence-triage-proposal.md) preserves the existing positive-review
requirement for `useful`. New synthetic inconclusive/fail review cases verify that
human utility notes do not override that gate, and that an explicitly authorized
`unclear` closure retains the result, signed review, frozen context and exact receipt
replay. Closure retries remain idempotent and later reclassification is denied.
The evidence suite returned **9 passed**; a separate adversarial reviewer independently
ran both new cases and requested a clarification of admission versus consent checks.
The full native suite returned **117 passed, 1 skipped**, with the existing upstream
deprecation warning. The live campaign remains unresolved: the maintainer's positive
utility judgment is recorded privately, but approval of the proposed terminal label
has not been received. No source policy, checker, grant or live disposition changed.

### Snapshot audit-log consistency, 2026-09-09

The operator backup command now checks existing audit-event links and canonical
digests on the closed private snapshot before no-overwrite publication. Four regression
cases altered an event payload, previous link, event hash or JSON syntax while SQLite
integrity and foreign-key checks still passed. They published under the prior code;
the new check rejects each without repairing the source, publishing a destination or
leaving staging files. The existing clean live-WAL/process-loss snapshot still passes.
The focused backup suite returned **8 passed**. This verifies internal consistency,
not coherent-rewrite resistance, detection of suffix deletion or unlogged changes,
independent witnessing, or safe restoration of old state.
The full native Windows suite returned **115 passed, 1 skipped**, with the existing
upstream deprecation warning. Independent adversarial review repeated the eight backup
checks and found no blocker. A fresh private pilot snapshot passed the new audit check;
the live database was neither restored nor replaced. No campaign, grant or policy changed.

### Bounded Windows state replacement retries, 2026-09-09

A disposable local reproduction held the state file open for reading and observed
`PermissionError` / Windows error 5 from `os.replace`; closing the reader allowed the
same save to succeed. This establishes a possible failure mechanism, not which process
or condition caused the earlier intermittent test failure.

The save path now retries only the already-closed, flushed staged replacement on
Windows errors 5, 32 or 33. Three total attempts add at most two 50 ms retry waits.
Permanent denial still propagates; the destination is never deleted or chmodded and
the enclosing operation is not replayed. Tests exercise an actual held Windows reader
that releases after failure, one that remains open through exhaustion, identical
staged path/bytes, unchanged durable state on failure, temporary cleanup and immediate
failure for unrelated I/O errors. The failed-renewal CLI regression remains passing.
Independent adversarial review ran the four focused cases successfully and found no
blocker. This is bounded contention handling, not a new power-loss durability claim.
Native Windows validation returned **111 passed, 1 skipped**, with the existing
upstream deprecation warning. Compilation, source privacy and whitespace checks passed.
The live helper and frozen campaign were not restarted or modified.

### Contributor lock diagnostics, 2026-09-09

Recognized nonblocking lock-contention errors now produce a fixed, actionable startup
message. Unexpected lock errors and invalid private state retain generic handling.
No private exception text is printed, and lock ownership, consent and process lifetime
are unchanged. A real second CLI process is refused while the first holds the lock;
the regression checks unchanged saved state, no secret/path disclosure, and reconnect
after release. An injected I/O error also verifies that unrelated failures are not
misclassified as another active helper. The contention test failed on the prior
generic diagnostic and passed after the change. Independent adversarial review ran
the real contention and release tests successfully and found no blocker.

The first full native run encountered a Windows access-denied error at `os.replace`
in an existing release/restart test: 107 passed, 1 failed, 1 skipped. The persistence
code was unchanged. A subsequent targeted run covering that release test and both
diagnostic regressions returned 5 passed. The destination was writable when inspected;
the cause of the earlier error remains unknown. This is not described as a fixed
filesystem defect or proof of recovery from arbitrary write failures.
The subsequent full native Windows run returned **108 passed, 1 skipped**, with the
existing upstream deprecation warning. Compilation, source privacy and whitespace
checks passed. No live helper was restarted and no campaign, grant or policy changed.

### Helper evidence pilot follow-up, 2026-09-09

A contributor on the second machine, as reported by the operator, returned a signed
source-evidence producer packet. Private coordinator inspection confirmed a shape-valid
candidate in `in_review`, with no review receipt or human disposition yet. This is
evidence of a recorded submission, not a verified defect or completed two-root cycle.
The contributor reported that its session lacked a callable native scheduling tool;
no remote hourly schedule was established. Local desktop model turns separately
reported missing contributor tools despite a configured, running helper. SDK discovery
and running processes did not resolve that integration gap.

The local connection subsequently recovered after stopping only the verified idle
helper that held the invite's OS lock and retrying the existing desktop worker task.
A fresh stdio status call first confirmed unchanged consent and no live assignment.
The actual desktop model then called the contributor tools, received the scheduler's
adversarial assignment and submitted a signed inconclusive review. Private coordinator
inspection confirmed that review against the earlier producer packet. Both contributor
steps have recorded receipts; the finding remains `in_review`, correctness unverified,
and human disposition unset. This was an interactive retry, not a verified hourly wake.
No new identity, consent renewal, coordinator restart or code change was needed for
the connection recovery. Recurrence of idle-session lock contention remains possible;
use one active helper session per invite.

Maintainer triage of the full frozen baseline found that `renew_consent` is called
only from the one-shot CLI branch, which exits on a persistence error before MCP
startup. The helper does not expose renewal as a tool. A new regression exercises
that actual CLI/renewal/save path with failure injected before atomic replacement;
it checks exit status, no MCP startup, unchanged durable consent on restart, no
assignment consumption, and released host lock. This narrows the reported concern
to hypothetical reuse of a failed in-memory object outside the production caller.
It is not a power-loss test or a claim about every filesystem failure. Contributor
artifacts remained inert; the regression was authored and run by the maintainer.
The packet's final usefulness classification still requires human disposition.
Native Windows validation returned **106 passed, 1 skipped** with the existing
upstream deprecation warning. Adversarial review independently ran the new targeted
test and requested an explicit assertion that failure injection was reached; that
assertion was added and the targeted test passed again. Source privacy and whitespace
checks passed. CI for this follow-up must be checked separately from earlier revisions.

Eight bounded repetitions of the previously intermittent real stdio submission and
restart test passed. The earlier `UnexpectedToolError` remains unreproduced, with no
established root cause. No repair claim follows from these passes.

Future changes should record exact tested versions, commands, supported hosts, evaluator digests and failure cases. Do not claim a missing integration passed because the core tests did. Store private logs outside Git and publish only sanitized summaries.

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

Future changes should record exact tested versions, commands, supported hosts, evaluator digests and failure cases. Do not claim a missing integration passed because the core tests did. Store private logs outside Git and publish only sanitized summaries.

# Bootstrap validation record

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

# Instructions for agents working on this repository

## Start

Read README.md, docs/architecture.md, docs/protocol.md, docs/threat-model.md and docs/roadmap.md. Report the distinction between implemented, tested, scaffolded and planned. Never invent benchmarks, tool results, successful CI, mathematical proofs or provider compatibility.

Use the approved WSL/Linux Python environment for development. Retain Windows contributor compatibility. Do not introduce a frontend framework, a worker daemon, Kubernetes, a blockchain, or extra services without an approved need. Run tests with `python -m pytest -q`; the demo is `python -m daia.cli demo` after installation or with `PYTHONPATH=src`. Do not claim optional integrations were tested if dependencies were unavailable.

## Invariants

Authentication derives the contributor root; a body cannot choose it. Agents cannot choose jobs, review targets, verification modes, reviewers or their own priority. Same-root keys cannot self-review or fill several modes for one candidate. Exposure history survives lease release/expiry. Leases have a hard deadline; old assignments cannot submit after reassignment. Receipts and follow-on work are idempotent. Freeze policy and context hashes before work starts. A trusted check failure is never overruled by agent consensus.

User consent, stopping and refusal are mandatory. Job budgets are not provider quota percentages. Do not collect provider account credentials, circumvent limits, or imply provider approval.

## Authority boundaries

Do not merge, deploy, change repository visibility, weaken security policy, change approval gates or obtain broader credentials as part of an assigned coding job. Proposals affecting these boundaries require maintainer review under the old policy. Candidate-controlled tests/logs are not independent verification. Do not execute untrusted payloads in the coordinator process or on a credential-bearing personal machine.

## Privacy

Use only public pseudonyms and noreply commit metadata. Never paste personal details from a user conversation or connected account into this repo. No real emails, names, business domains, locations, private project names, private paths, transcripts or client information belong in examples. Never commit `.env`, provider tokens, private keys, `.runtime`, `.private`, database files, logs, caches or output from `invite`.

Run `python scripts/privacy_guard.py --history` before publication. Do not echo any sensitive matched values; identify a safe object reference and category only. Do not assume `.gitignore` removes already tracked content.

## Handoff

Keep changes scoped, add regression tests, include actual command outcomes, and document unresolved risks. Update status tables only with evidence. Dependencies need a reviewed lock and vulnerability audit before release. Licensing remains a maintainer decision.

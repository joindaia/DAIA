# Contributing

DAIA is licensed under [AGPL-3.0-or-later](LICENSE-STATUS.md). By intentionally
submitting a contribution for inclusion, you offer it under the same license and
retain your copyright, where applicable. You must have authority to submit the
material; identify third-party code and preserve its license and notices. Do not
submit material with incompatible terms. There is no copyright assignment.
Commercial relicensing requires a separate explicit grant to an identified legal
steward; contribution under AGPL alone does not provide it. See the
[commercial policy](docs/commercial-licensing.md),
[supplemental grant draft](docs/contributor-commercial-grant.md) and
[rights register](docs/licensing-rights-register.md). Until a final grant is executed,
contributions remain AGPL-only for this purpose. A public
pseudonym is welcome; keep private identity and account details out of commits.

Start with a bounded issue stating the objective, acceptance criteria, baseline, scope and evidence
plan. Use the development-task template for a proposed improvement and the bug template for a
reproducible defect. Keep the issue small enough for one reviewable change; split unrelated work.
Preserve the assignment, ownership, signature, lease and verification invariants in AGENTS.md.
Include a failing regression test before a behavioral fix. For concurrency changes, add real
multi-process database tests rather than relying solely on in-memory unit tests.

Choose the contribution type explicitly. Source analysis supplies a bounded finding and supporting
references; it does not execute contributed code and remains subject to authorized maintainer triage. A trusted
local code change is implemented and checked by a maintainer or trusted local contributor. The
two-agent technical pilot may supply feedback, but shared ownership means its review is never
independent verification, approval or authority to merge.

Run unit tests, the deterministic demo and the privacy guard. Distinguish what ran locally from what has not run on Windows, MCP hosts, production storage or GitHub CI. Do not paste raw tokens, payloads, databases or personal logs into the PR.

All merges require a separate maintainer decision. Routine DAIA integration may be
performed under the [standing owner delegation](docs/maintainer-delegation.md).
Assigned worker reviews are evidence, not permission to merge their own submissions. Protected changes must not weaken the checks required for their own acceptance. This
repository does not assume paid GitHub branch-protection features: templates and CI communicate
the process, while a maintainer enforces it at review and merge time.

The project values small reproducible improvements over large speculative rewrites. Begin with the next uncompleted acceptance gate in docs/roadmap.md.

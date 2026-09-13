# Contributing

DAIA remains [AGPL-3.0-or-later](LICENSE-STATUS.md). Submission alone transfers
no copyright. Contributors currently retain rights they actually hold unless a
separate valid instrument says otherwise. You must have authority to submit the
material, identify third-party code and preserve its licence and notices.

The selected target is [foundation ownership of accepted new Core contributions](docs/core-rights-decision-2026-09-13.md),
with the public AGPL edition preserved and foundation-only alternative licensing.
No assignment workflow is active yet. New external copyright-relevant Core needs
an executed, applicable instrument before it can be accepted as ownership-cleared.
An expressly approved AGPL-only exception must remain recorded as such. Research
and proposals can be reviewed without being assigned; unrelated job outputs are
outside this policy. Do not treat an agent key, PR submission or checkbox as a deed.

See the [rights register](docs/licensing-rights-register.md) and
[commercial policy](docs/commercial-licensing.md). Public pseudonyms are welcome;
legal identity and agreement evidence belong in restricted records, never commits.

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

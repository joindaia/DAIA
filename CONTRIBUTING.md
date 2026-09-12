# Contributing

This is a pre-publication scaffold. A contribution license has not yet been selected; maintainers should choose and document one before accepting outside contributions. Do not assume that a public repository automatically grants an open-source license.

Start with a bounded issue stating the objective, acceptance criteria, baseline, scope and evidence
plan. Use the development-task template for a proposed improvement and the bug template for a
reproducible defect. Keep the issue small enough for one reviewable change; split unrelated work.
Preserve the assignment, ownership, signature, lease and verification invariants in AGENTS.md.
Include a failing regression test before a behavioral fix. For concurrency changes, add real
multi-process database tests rather than relying solely on in-memory unit tests.

Choose the contribution type explicitly. Source analysis supplies a bounded finding and supporting
references; it does not execute contributed code and remains subject to human triage. A trusted
local code change is implemented and checked by a maintainer or trusted local contributor. The
two-agent technical pilot may supply feedback, but shared ownership means its review is never
independent verification, approval or authority to merge.

Run unit tests, the deterministic demo and the privacy guard. Distinguish what ran locally from what has not run on Windows, MCP hosts, production storage or GitHub CI. Do not paste raw tokens, payloads, databases or personal logs into the PR.

All merges require a human maintainer. Reviews from agent identities are evidence, not permission
to merge. Protected changes must not weaken the checks required for their own acceptance. This
repository does not assume paid GitHub branch-protection features: templates and CI communicate
the process, while a maintainer enforces it at review and merge time.

The project values small reproducible improvements over large speculative rewrites. Begin with the next uncompleted acceptance gate in docs/roadmap.md.

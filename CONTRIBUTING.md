# Contributing

This is a pre-publication scaffold. A contribution license has not yet been selected; maintainers should choose and document one before accepting outside contributions. Do not assume that a public repository automatically grants an open-source license.

Start with an issue stating the objective, acceptance criteria, baseline and scope. Preserve the assignment, ownership, signature, lease and verification invariants in AGENTS.md. Include a failing regression test before a behavioral fix. For concurrency changes, add real multi-process database tests rather than relying solely on in-memory unit tests.

Run unit tests, the deterministic demo and the privacy guard. Distinguish what ran locally from what has not run on Windows, MCP hosts, production storage or GitHub CI. Do not paste raw tokens, payloads, databases or personal logs into the PR.

All initial merges require a human maintainer. Reviews from agent identities are evidence, not permission to merge. Protected changes must not weaken the checks required for their own acceptance.

The project values small reproducible improvements over large speculative rewrites. Begin with the next uncompleted acceptance gate in docs/roadmap.md.

# Contributing

DAIA remains [AGPL-3.0-or-later](LICENSE-STATUS.md). Intentional submissions for
inclusion are offered under that licence to the extent you have authority; submission
alone neither assigns copyright nor grants proprietary relicensing rights. Disclose
third-party material and preserve its licence and notices.

The [current proposed model](docs/licensing-model-v2.md) retains contributor copyright
and adds a separate, explicit commercial/patent grant for qualifying accepted Core
contributions. Its recipient may be an identified company, including a founder-owned
company, or an optional foundation. No CLA acceptance or commercial programme is
active. No agreement is executed by a PR checkbox, worker key or this page.

Before external Core work is commercially cleared, an actual rights holder must
have accepted an applicable reviewed instrument, with employer/organizational authority
where needed. Future worker work needs prior scoped authorization and an exact
acceptance record; unrelated jobs and rejected output are not captured. Tests and
documentation can contain copyright-relevant material too. Research/proposals may
be reviewed under existing permissions. An expressly approved AGPL-only exception
must remain labelled and cannot silently enter a proprietary-cleared release.

See the [grant architecture](docs/contributor-commercial-grant.md) and
[rights workflow](docs/licensing-rights-register.md). Public pseudonyms are welcome;
legal identities and agreement evidence belong in restricted records, never commits.
Existing signed grants are not changed by this proposed policy.

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

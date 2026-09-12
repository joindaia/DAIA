# Mission: build DAIA, then attempt a Millennium Prize Problem

DAIA's long-term goal is to coordinate a serious attempt at a still-open Millennium
Prize Problem. First, use the platform to improve DAIA itself and demonstrate that
agents can produce useful, checked work with less routine maintainer intervention.
No particular problem, solution date, success probability or prize income is promised.

## 1. A working software-development loop

Use two existing agents for bounded source analysis and technical review. The
orchestrator chooses a real issue, prepares the frozen context, inspects the returned
evidence, implements justified changes on a branch, and opens a PR with actual tests.
A human decides whether to merge. An analysis receipt is an intermediate deliverable;
a passing test count or a busy queue is not a completed software improvement.

Before expanding into research, record three consecutive completed development rounds
with an issue, actual scheduled producer/reviewer receipts, disposition, a tested
change or an honest no-change conclusion, and a human merge/disposition decision. Record maintainer interventions and elapsed work
per round; do not invent a baseline or claim improvement without a comparison.
At least two rounds should require human action only for initial authorization and
final merge/disposition; log every other intervention. At least one round must
recover from an interrupted transport without lost receipts, reset allowance,
duplicate accepted work or manual database repair. If a round finds no
defect, retain that result honestly rather than manufacturing a fix.

The numerical round count is an acceptance target, not current measured performance.
Existing frozen campaigns retain their rules. Pilot reviews can share an owner and
are explicitly not independent; no new contributor identity is needed for this phase.
Check CI on the exact reviewed commit, and demonstrate that a deliberately failing
change is rejected by CI before calling the gate reliable. GitHub CI and templates
support review without pretending to enforce unavailable branch protection. See [GitHub workflow](github-workflow.md).

## 2. Demonstrate trustworthy mathematical work

Choose a small, published mathematical problem and freeze its exact statement and
allowed assumptions. Reproduce a known result before attempting a novel one.
Build and test an isolated proof-checking environment without coordinator secrets,
provider credentials or personal filesystem mounts. Contributor-supplied proof code
must not execute on the coordinator or a credential-bearing machine.

Record proof artifacts, checker/toolchain versions, dependency hashes, allowed axioms
and trusted checker results. Challenge malformed statements, hidden assumptions,
unproved placeholders, resource-limit violations and incorrect claims. A second model's agreement is not a
proof check, and a proof checker does not establish that we formalized the right
problem. Have a qualified human examine the statement and assumptions.

## 3. Select and run the research campaign

Recheck the official status of candidate Millennium Prize Problems and published
claims at selection time. Select one problem and decompose its prerequisites and
lemmas into bounded research tasks. Start with a finite pilot budget, an evidence
plan and explicit stop/review points. Useful partial results also count as research;
only a valid solution to the actual problem counts as solving it.

Recruit mathematical expertise for independent examination. Freeze attribution and
reward terms before inviting contributions to the prize campaign. Existing software
pilot participation does not silently enroll anyone in research or create a payout
entitlement. Decide explicitly whether, and how, earlier platform-building work is
included in that campaign's contributor pool.

## Other paid work

Authorized bug bounties and customer-requested deliverables may provide nearer-term
paid work after platform readiness. They have their own scope, acceptance and consent
contracts; they do not inherit Millennium eligibility or a reward promise. See
[paid-work design](paid-work.md).

## Reward intent

If the campaign qualifies for and actually receives a prize, the intent is to share
the contributor pool among all eligible contributors according to accepted
contribution, after a disclosed platform share for DAIA's running costs. The platform
percentage, valuation method, treatment of supporting work and earlier contributions,
duplicates, dependency credit, disputes, costs and payment eligibility still need
agreement before work starts. Value must not be assigned retrospectively only after
a promising solution appears; supporting lemmas, review and earlier work need a
pre-agreed treatment. Raw job counts, token use and extra identities must not determine rewards.

No funds are held or distributed by this implementation. A signed finding does not
establish prize eligibility, authorship rights or an amount owed. See [reward issue
#6](archived project reference) for the proposed allocation work.

## Research context checked on 2026-09-09

OpenAI [announced a Navier–Stokes solution](https://openai.com/index/navier-stokes-solution/)
and says it does not intend to claim the Millennium Prize. This is an announced
research result, not evidence that DAIA can reproduce it or that Clay awarded a prize.
Anthropic's [Riemann-zeta work](https://www.anthropic.com/research/riemann-zeta) reports
progress on a related bound, not a solution of the Riemann hypothesis. Its
[Fermat formalization](https://www.anthropic.com/research/formalizing-fermats-last-theorem)
checks a previously proved theorem; it is not a new Millennium solution.

[Clay's published rules](https://www.claymath.org/millennium-problems/rules/) require
qualifying publication, at least two years and general mathematical acceptance before
consideration; proposed solutions are not submitted directly to Clay. The rules and
[current problem list](https://www.claymath.org/millennium-problems/) must be checked
again before choosing a prize target. Scientific progress and prize adjudication are
separate milestones.

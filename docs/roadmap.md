# Roadmap and acceptance gates

No dates, unmeasured budgets, or research-success probabilities are promised.
The website presents a dated [public roadmap](../website/src/pages/roadmap.astro).
The [public launch brief](public-launch.md) defines the next hosting and onboarding
work, with conditional estimates and a separate boundary for executable jobs.

## Project goal

First make DAIA a reliable, increasingly autonomous software-development platform.
Then demonstrate isolated proof verification on smaller mathematical tasks and
coordinate an attempt at a still-open Millennium Prize Problem. Any actually received
prize would be shared under a contributor allocation policy agreed before the campaign,
including a disclosed platform share. This is a research goal, not promised income.
See [mission and measurable gates](research-mission.md).
Authorized bug bounties and customer job requests are possible paid routes alongside
the research goal, after the platform can deliver and verify bounded work. Start with
a sample contract and shadow cost record; see [paid-work scope](paid-work.md).

## Active security milestone

The authorized [compromised-coordinator milestone](compromised-coordinator-milestone.md)
adds signed releases, a startup integrity gate, independently authorized jobs and
local worker isolation to the closed HTTPS cutover. These controls are being
implemented; public cohort admission remains empty until their deployment gates pass.

## Immediate product sequence

This ordered sequence governs the next work. The longer-term architecture sections
below are dependencies and options, not a requirement to build every subsystem first.

| Milestone | Evidence required | Current status |
|---|---|---|
| One useful scheduled two-host cycle | Actual scheduled wakes, assigned producer/reviewer receipts, explicit technical-pilot assurance, attributed maintainer triage and one checked, integrated improvement | As of 11 September: pilot-eligibility analysis and supporting technical review submitted; round closed as useful source analysis, with no defect established. Writing round admitted. A checked and merged improvement from a complete scheduled cycle is still unestablished |
| Repeatable human decisions | Exact proposal and consequences shown in a native question; approved choice revalidated and recorded without changing the review | Implemented and tested; first live preview, native choice and verified resolution completed |
| Repeatable development rounds | Prepared relevant work, explicit finite participation, reliable installation, recorded receipts and clear pause reasons | Server extension and local acceptance implemented/tested; existing local worker connection recovered and native hourly schedule resumed within existing consent. Actual scheduled completion remains to be observed |
| Demonstrated development value | Useful checked improvements with recorded review effort and fewer maintainer interventions | Not yet measured; test counts and idle wakes do not establish value |
| Durable general human consultation | A concrete blocked task requires stored questions and answer-based resumption | Deferred by maintainer; existing host questions and triage are sufficient now |
| Safe executable contributions | Untrusted code runs only in an isolated evaluator, with independent trusted results | Planned; source evidence remains inert |
| Wider participation and rewards | Provider/licensing/privacy review, measured useful contribution and explicit allocation policy | Planned; no public service or payouts |

Each development wake must name the milestone and its next unmet acceptance check.
Finish the current slice before selecting another. When a human answer or worker is
pending, complete independent work within that same slice. After that, advance the
next reviewed product slice instead of searching indefinitely for small hardening
changes. Security or data-loss defects still interrupt this order when demonstrated.
Do not treat test counts, empty polling or a configured schedule as product completion.

The [2026-09-09 heuristic boardroom](boardroom-2026-09-09.md) records the current
multi-model discussion, adversarial corrections and ordered continuation. Native
scheduled prompts, finite consent renewal and the bounded source-evidence workload
are implemented. See [hourly workers](hourly-workers.md) and
[evidence campaigns](evidence-campaigns.md) for their authority and validation limits.
The immediate acceptance gate is a real scheduled two-worker evidence cycle and a
maintainer-accepted useful outcome. The [prepared backlog](development-backlog.md) keeps
the next three slices concrete without admitting concurrent campaigns. General human
consultation remains host-native; durable waiting/resumption is deferred until a real
task needs it. Isolated contributed-code execution remains planned.
Worker-dependent acceptance gates do not block independent local engineering. While
the pilot awaits contributors or maintainer disposition, improve repeatable participation
and prepare relevant work on the review branch without admitting more live campaigns
or changing live policy. [Private snapshots](recovery.md) now have a
synthetic WAL/process-loss recovery exercise; real restore and reconciliation remain
maintainer operations.

The maintainer approved an opt-in two-agent technical pilot for new campaigns.
Shared ownership is allowed and labeled as not independent; old campaign rules stay
frozen. See [pilot operation](evidence-campaigns.md#optional-two-agent-technical-pilot).
The eligibility-analysis round now has producer/reviewer receipts and an explicit
individual owner disposition. The writing round is active. Next, establish a useful
checked improvement and its scheduled-worker provenance; no third agent is needed.

The owner granted [standing maintainer delegation](maintainer-delegation.md) on
11 September. Routine campaign triage and continuation now use that authorization,
with decisions attributed to the maintainer. The earlier requirement for a fresh
owner answer at each round no longer governs routine work. Worker review, consent
and isolation rules remain intact. Development stays within DAIA and involves no
external outreach.

## Delegating orchestration

The [shared-orchestration milestone brief](delegated-orchestration.md) defines the
next direction: delegate planning, measure total review and coordination overhead,
then propose scoped, revocable capabilities while the owner retains final execution
authority. Shared voting and agent promotion start as shadow recommendations, not
live powers. This does not bypass the current pilot or change frozen campaign rules.
The brief names a process-boundary receipt-recovery exercise as independent work
while host setup or an assigned review is pending. Its completed exercise is recorded
in that brief.

## 0. Safe bootstrap — reference implementation

Implemented: bounded certificate workload, durable local leases, grant expiry, owner conflicts,
signed registration/results, blinded reproduction, adversarial evidence, deterministic checks,
local REST adapter and regression tests. MCP 2.2.0 protocol tests and Codex CLI discovery now
pass on Windows. The two-client tailnet pilot subsequently completed signed reviews and
promotion, with host placement reported by the user. The desktop-helper change subsequently
passed Windows and Ubuntu CI in archived project reference.
Maintain the tested/untested distinction in README and `docs/validation.md`.

## 1. Real agent interoperability — next engineering milestone

The portable dependency lock and local vulnerability audit are complete. Two actual
clients completed the raw-protocol pilot. The desktop/CLI signing helper now has real
stdio-to-HTTP process tests, persistent consent, native Codex discovery and failure
recovery checks; repeat the human two-machine pilot using this helper. AGPL-3.0-or-later
has been selected; distribution-specific dependency reviews, OS-bound signing, public
OAuth/OIDC and production consent remain open. Native Windows
instructions require no WSL or provider-token collection.

Exit: an authorized human connects a host, completes bounded assigned work and reviews an independently checked result; revocation/stop prevents new work; no secrets appear in tools, logs or commits. Do not use a subscription-percentage control without actual supported metering.

## 2. Trusted pilot and production storage

Use invite-admitted contributors and an explicit threat model. Implement PostgreSQL transactional claim/receipt/outbox semantics with multi-process fault tests. Add bounded retention, ingress limits, backup/restore, observability and safe contributor-root recovery. Run adversarial tests for multi-key and multi-root attacks, release-shopping and reviewer starvation. Introduce adjudication/retry workflows before accepting general research.

Exit: demonstrated durable behavior and measured review costs under failures. No public permissionless independence claim.

## 3. Independent verification workers

Add a minimal pinned Lean problem with approved assumptions and a specification checker, on isolated infrastructure separate from coordinator credentials. Return authenticated checker receipts. Extend policies per workload and add reproducibility bundles, dependencies, approved context material and content-addressed artifacts. Add a controlled code-verification sandbox only after threat review.

Exit: submitted malicious code cannot access host credentials; a changed theorem, unapproved axiom or forged success log cannot pass.

## 4. Bounded platform-improvement project

Allow consented contributions to a fixed baseline and evaluator. Use independent reproduction, held-out tests and separate authorized maintainer integration. Start with a regression fixture or read-only optimization. Track validated improvement rather than throughput theater. Add protected environment/branch enforcement before any release automation.

Exit: one real useful change produced, independently validated, reviewed and manually merged through DAIA's workflow.

## 5. Public readiness

The sanitized source history has been reviewed and AGPL-3.0-or-later selected; see
[the licensing decision](licensing-decision.md). Repeat privacy and dependency reviews
for each release artifact. Enable appropriate repository protection, private vulnerability reporting, contributor guidelines, provider integration/terms review and a real consent policy. Document what data donor-host providers see. Publish a supported-client matrix and tested resource limits. Re-audit all release artifacts, actions logs and public account linkage.

Only then consider broader admission, reputation calibration, a read-only UI, reusable research DAGs, scoped public attestations, independent transparency witnesses and federation. Bounty payouts, governance voting, tokens and financial claims are separate projects, not implicit features of signed agent contributions.

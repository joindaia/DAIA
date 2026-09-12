# Heuristic boardroom: useful work, native scheduling and human judgment

This is a recorded engineering discussion, not empirical validation, a vote on truth,
or evidence that different models are independent people. The user authorized a
multi-model boardroom, adversarial challenges, hourly orchestration and continued
implementation. Test and pilot results remain separate from these judgments.

## Product-focus follow-up

### Finite continuation follow-up

The maintainer deferred durable human-question storage and asked for longer recurring
participation and prepared work. The existing engineering/adversarial reviewer and
the GPT-5.6 Sol / high product reviewer both supported a minimal server-side extension
as a prerequisite, with absolute limits and existing transactions instead of a new
service or grant schema. They required preserved identity, used work, exposure,
cooldown, revocation, receipts and independent local consent; exact retries must add
neither capacity nor audit events. The actual implementation passed independent
extension/HTTP checks with no blocking findings.

The product reviewer challenged expiry behavior: refusing expired grants means this
path must run before existing expiry; allowing them would reactivate an old bearer
token. The current proposal explicitly refuses expired and revoked grants under the
existing boundary. Later same-root recovery or token rotation needs separate review;
fresh roots are not a workaround. The helper's original invite expiry and 24-hour
window remain enforced. No live extension, schedule restart or completed week-long
participation is claimed. See [operator extension](hourly-workers.md#operator-grant-extension-server-side-prerequisite).

### Earlier native triage follow-up

The maintainer challenged continued small reliability fixes as insufficient product
progress. A new GPT-5.6 Sol / high product reviewer and the existing adversarial
reviewer both recommended a complete native triage handoff as the next bounded
slice. Both challenged a standalone preview command as mere operator polish: its
packet must be used in a real native question, then the chosen action revalidated.
General durable human-input suspension/resumption was deferred until an explicit
lifecycle/privacy design; preparing more campaigns does not resolve the present gate.

The implementation uses `resolve-evidence --dry-run` through the existing resolver,
preserving the v1 supporting-review requirement. The adversarial review required
recorded-state cancellation counts, no lease-expiry processing, exact notes,
zero-effect idempotent previews and explicit snapshot limits. The first live preview
left the logical database snapshot unchanged and was presented through a native
choice. The maintainer explicitly chose `unclear` with the utility note. A refreshed
preview matched, and the original resolver applied the decision. Verification found
one new resolution event, no unresolved campaign, and unchanged signed evidence,
review, grants and assignments. No next campaign was admitted by that action.
Model agreement is design input, not permission to choose for the maintainer.

The [immediate roadmap sequence](roadmap.md#immediate-product-sequence) now governs
hourly selection: name the milestone and unmet acceptance check, finish that slice,
then advance the next reviewed product slice. Demonstrated security/data-loss defects
may interrupt; routine hardening must not become an indefinite substitute for the
scheduled useful cycle, human consultation and isolated execution milestones.

| Participant | Configured model / reasoning | Role and contribution |
|---|---|---|
| Engineering | GPT-5.6 Sol / high | Traced consent and scheduling; implemented and tested explicit finite renewal |
| Incentive adversarial | GPT-5.6 Luna / medium | Challenged empty polling, proposal volume, reward gaming and false consensus |
| Protocol adversarial | GPT-5.6 Terra / xhigh | Found replayable reviews and provenance gaps; required distinct review and frozen schemas |

An attempted GPT-6 Astra / xhigh participant remained pending initialization and was
interrupted. Its nonexistent findings did not contribute to this record. The primary
orchestrator compared the actual responses, requested rebuttals and owns the decisions
below. Model labels and reasoning settings are configuration, not a measured ranking.

## Decisions and disagreements

1. Use native scheduled prompts. MCP lease heartbeats do not wake a stopped agent.
   Each worker wake makes one claim, completes at most one job, and ends. Empty wakes
   are idle outcomes. There is no custom daemon or inferred provider-quota percentage.

2. Fix finite consent before recurring work. A 30-minute setup could never serve an
   hourly wake once it expired. Renewal is a one-shot owner action on the same key
   and root, capped by live grant capacity and original expiry. Startup flags and
   scheduled prompts cannot reset usage, revive stopping or renew themselves.

3. Start with source evidence rather than submitted code execution. Freeze one small
   Git excerpt, objective, schemas, checker and policy. Accept bounded findings and
   a distinct candidate-bound adversarial report. Structural validity is explicitly
   separate from correctness. The first useful result is a human-dispositioned packet
   that leads to a checked improvement, not a count of completed model turns.

4. Keep one unresolved campaign. Admission is content/policy-idempotent across hourly
   wakes and resolution. Human triage clears the campaign; automation cannot invent a
   disposition to make space. Stalled, rejected and inconclusive work remain visible.

5. Use a new narrow policy for two worker roots. Engineering initially proposed two
   review modes, which would require a third admitted root. The incentive reviewer
   supported producer + one adversarial root + mandatory human disposition as an
   explicitly limited evidence experiment. The protocol reviewer agreed after the
   review schema was separated and bound to the candidate. Existing math policies
   are unchanged. No correctness, promotion, payout or independent-human claim follows.

6. Separate operator delegation from worker authority. The protocol reviewer initially
   opposed autonomous admission, then retracted that blanket restriction after the
   user's explicit orchestration delegation was clarified. The orchestrator may
   prepare and admit bounded targets; workers cannot select them or access admin MCP
   tools. Human disposition and merge/deployment/payout decisions stay separate.

7. Reuse native human consultation for any task. Ask for judgment, interpretation,
   priorities, preferences or a sanity check using ordinary Codex questions, choices,
   and interactive examples where helpful. Design is one use case. No questionnaire
   or MCP elicitation subsystem is needed merely to use those host capabilities.
   Durable waiting and resumption require a later explicit context-versioning design.

## Adversarial findings applied

- Producer-text replay could satisfy the first review shape. The reviewer now has a
  separate schema, a candidate digest, an assessment tied to verdict, objections and
  a next check. Tests reject producer replay and wrong bindings for every verdict.
- A commit-shaped string was not source provenance. Operator CLI admission now reads
  the real Git object and compares exact lines, including line endings. Core service
  metadata remains labeled as operator-supplied rather than independently witnessed.
- A context hash did not explicitly identify its schemas/checker. Both schema hashes
  and the trusted checker source hash are frozen; mismatches fail closed.
- Local expiry and original grant expiry are different. Explicit renewal may renew a
  locally expired window while the original grant is live; ordinary wakes may not.
- Human questions do not suspend leases. Today a blocked worker must report uncertainty
  or release work; silence and programmatic responses are never human authorization.

## Ordered continuation

Maintainer update: general human consultation is deferred. The immediate sequence
in [roadmap](roadmap.md) and its [development backlog](development-backlog.md)
supersedes item 3 below. Prioritize a complete useful cycle, repeatable finite
participation and evidence of reduced maintainer effort. Existing native questions
remain available without a durable question subsystem. The historical discussion
below records the earlier recommendation, not authority to implement it now.

1. Verify one real native scheduled worker cycle with the helper on each host, finite
   consent and a fixed evidence campaign. Record empty wakes, claims, receipts,
   disagreement, uncertainty and human disposition; do not create activity for its own sake.
2. Convert one useful packet into a small maintainer-authored change with targeted
   regression coverage and manual merge. Submitted commands and patches remain inert.
3. Add durable `needs_human_input` and resumption with a newly frozen context, explicit
   visibility of what answers are shared, and no indefinite lease retention. Keep
   opinion, verified facts and authority decisions distinct.
4. Add bounded adjudication/retry and actual process-loss/retention/restore exercises.
   Scale storage only after measured contention or operational requirements justify it.
5. Introduce isolated code/proof verification before admitting executable artifacts.
   Keep trusted evaluator receipts and held-out checks outside candidate control.
6. Test the prize-sharing idea from archived project reference
   with shadow accounting after useful contribution measurement exists. Freeze a
   disclosed platform share and contributor allocation before any paid campaign;
   eligibility, accounting, privacy, abuse controls and human payout approval remain open.

At each step, the gate is actual evidence of useful work and safe stopping. A busy
queue, several model opinions, or a passing transport test alone cannot satisfy it.

## Independent continuation

The user clarified that waiting for worker activation must not reduce continued
development to monitoring. Worker-dependent evidence gates still apply, but independent
recovery and failure-handling work may proceed on the review branch. The first such
increment is the [private snapshot and recovery exercise](recovery.md), using SQLite's
existing backup API. No new service, automatic restore or live policy change was needed.
The protocol adversarial participant reviewed the actual diff, required the distinction
between pre-snapshot stale leases and post-snapshot rollback, and reported no blocking
finding after independently running the 98-pass suite (one platform-specific skip).

## Maintainer-approved two-agent technical pilot

The maintainer chose a private pilot with two existing agents rather than requiring
another contributor. The orchestrating model proposed one opt-in frozen admission
policy, explicit non-independent context labels, no producer-agent self-review,
retained root-level review exposure and a distinct human-triage result status.
A separate GPT-5.6 Sol/high adversarial participant inspected the implementation and
reported no blocking correctness issue. It checked the old-policy boundary, CLI
forwarding, verdict handling and exposure/replacement-key tests, and independently
ran `git diff --check`. Full suite and MCP execution evidence were supplied by the
orchestrator, not independently rerun by that participant.

Decision: enable only for newly admitted source-evidence campaigns. Shared ownership
is acceptable for technical feedback, never independent approval. Existing frozen
campaigns retain their rules and disposition requirement; no new root or reset is
needed. One live lease per root and finite consent remain. General human-question
storage, automatic merge and rewards remain outside this increment.

## Development workflow, website and research goal

The maintainer made real DAIA development the near-term purpose, requested GitHub CI
without premium branch protection, and approved a static website preview. A separate
GPT-5.6 Terra/high participant implemented the scoped CI/templates/documentation work;
it validated YAML and the diff. The orchestrator built and browser-checked the website
and retained plain English copy focused on concrete tasks and outcomes.

For the subsequent Millennium Prize goal, GPT-5.6 Sol/high challenged the meaning of
"largely autonomous": three rounds can hide heavy intervention. The mission now sets
an explicit intervention threshold, real transport recovery, exact-commit CI evidence,
and isolated proof-checking gates. It also separates a proof claim from publication,
acceptance, award and funds received. Its principal attribution warning was adopted:
freeze contribution credit before promising results, rather than rewarding only the
last artifact or raw activity. These are readiness targets, not observed results.

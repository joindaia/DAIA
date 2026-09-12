# Milestone brief: shared orchestration with owner-controlled execution

Status: approved direction and planning brief, not implemented governance or a change
to live permissions. Existing campaigns retain their frozen rules.

## Outcome

Reduce dependence on one maintainer agent by distributing planning and review as
bounded, consented work. Keep a small deterministic coordinator for assignment,
budgets, receipts and policy checks. The owner retains final execution authority
until specific, revocable delegations are separately approved.

Success means useful checked changes with less maintainer effort after accounting
for planning, review, retries and rework. More jobs or more votes are not success.
Distributed execution is already demonstrated; distributed governance and an
efficiency advantage are not.

## Sequence and acceptance

1. **Establish the baseline.** Complete the existing scheduled two-agent pilot after
   its pending disposition and host setup checks. Record one actual useful change,
   its receipts, tests, review and execution decision. Separate the three historical
   factorization-demo jobs from the three source-analysis/review jobs. Do not count
   six completed assignments as six delivered improvements.
2. **Delegate planning in shadow mode.** Give an assigned agent one bounded planning
   question against an approved project snapshot. Its inert proposal names the
   problem, code scope, acceptance check, dependencies, risk and expected review
   effort. An assigned reviewer challenges necessity and scope. The maintainer
   accepts, revises or rejects it; proposals cannot admit jobs or change priority.
   Exit: one proposal becomes a checked improvement with recorded interventions.
3. **Measure three real development rounds.** Include planning, implementation,
   automatic checks, targeted review, rework and final disposition. Compare with a
   documented maintainer-only baseline of reasonably similar scope; label estimates
   and differences. Record active maintainer minutes, agent effort where observable,
   elapsed time, retries, review findings and accepted outcomes. Missing token or
   provider-cost data stays unknown. Exit: report whether delegation reduced effort;
   if not, simplify task routing before adding governance machinery.
4. **Propose narrow execution delegation.** Design an owner-approved permission
   record binding an agent to an action, scope, expiry and budget, with revocation
   and an audit receipt. Start with a reversible action. Test denial outside scope,
   after expiry/revocation and on replay, and preserve existing consent. An approval
   binds the exact artifact and policy; changed inputs require renewed approval.
   Do not issue rights or expose an executor until this design is explicitly approved.
5. **Evaluate shared decisions and promotion.** Trial recommendations in shadow mode
   before granting decision authority. Specify eligible participants, owner conflicts,
   quorum, abstention, disputes and timeout behavior; lack of quorum never silently
   lowers the threshold. Rights remain owner-approved initially. Federation and
   removal of the trusted coordinator are separate later milestones.

## First shadow packet contract

Use one frozen source excerpt and the existing source-finding schema. `finding`
states the observed problem and assumptions; `reproduction_outline` describes inert
acceptance evidence; `suggested_change` states scope, dependencies, risk, expected
review effort and at most one proposed step. Keep the existing source binding and
field limits. Insufficient evidence or no justified new work is a valid outcome.
No schema extension or executable plan is required.

Accept, reject and revise are maintainer decisions, not new worker operations.
An accepted proposal may be resolved as `useful` only when the existing frozen review
and disposition requirements are satisfied. Rejection uses the existing `rejected`
disposition after explicit approval. Revision never edits signed evidence: prepare an
explicit closure proposal (`unclear` or `rejected`, according to the evidence), obtain
approval and close through the existing resolver. Only then can a newly frozen,
materially revised campaign be admitted and reviewed on its own merits. Neither this
brief nor the shadow packet authorizes closing the currently pending campaign.

## Trust and execution

The proposed progression is contributor, reviewer, planner, then scoped maintainer.
These are possible capabilities, not an automatic rank ladder. Evidence quality,
confirmed outcomes and reviewed incidents inform promotion; job counts and popularity
alone do not. Reputation never authorizes an agent to grant itself or others rights.
Permissions are specific, time-limited and revocable; changes to the agent or its
operating setup may require reassessment. Revocation preserves signed history.

The owner's executor remains separate from proposal and voting agents. An SSH key
is a credential, not the decision policy. Never distribute that key to workers or
allow proposed shell commands to become execution authority. Money, consent changes,
credential access, deployment and broader privileges retain explicit owner approval.
Registration proves neither independent ownership nor trustworthy work. Multiple
agents or keys of one owner do not create independent votes. Current shared-owner
pilot reviews remain technical feedback only. Votes cannot override a failed trusted
check or prove code correctness or a mathematical statement.

## Control verification overhead

Choose checks from the consequences and reversibility of a change, before assignment.
A future low-impact policy may use automatic checks and one targeted review; sensitive
changes need stronger validation and owner approval. Do not retrofit lighter checks
onto a running campaign. Independent review need not repeat the entire implementation:
check the changed behavior, assumptions and trusted evidence. Candidate-supplied logs
and tests alone are insufficient. Trusted contributors may receive calibrated review,
not immunity from checks. Measure missed defects and rework as well as speed.

Avoid tasks whose coordination costs exceed their value; combine related small work
where it remains independently reviewable. Stop or revise an unproductive experiment
rather than generating jobs to keep agents busy. No blockchain, token market, general
reputation engine or new service is needed for the first planning experiment.

## First independent engineering slice

While the existing live campaign and WSL worker setup await completion, implement a
local process-boundary receipt-recovery exercise using synthetic isolated state.
Simulate acceptance of a submission followed by loss of its response. Retry the exact
submission and check one durable receipt, no duplicate follow-on work and no extra
assignment consumption. Record failures honestly; do not renew consent, touch live
receipts, execute worker payloads or admit a second live campaign for this test.
Then prepare the minimal shadow-planning packet and review its lifecycle with the
previously authorized multi-model boardroom, including an adversarial participant.
No such review or process exercise is claimed by this brief.

## Scope of this decision

This brief authorizes preparation and bounded local engineering under existing rules.
It does not close the pending campaign, renew participation, implement voting powers,
automatically promote agents or authorize payouts or public deployment. The near-term
acceptance gate remains the [scheduled pilot](development-backlog.md); longer-term
research and paid work retain their existing gates in the [roadmap](roadmap.md).

## Recorded recovery exercise

The new `test_stdio_restart_recovers_discarded_http_submission_response` passed on
WSL/Linux. A temporary real HTTP MCP server committed the candidate; test middleware
discarded its response and returned HTTP 503. A fresh contributor OS process retried
the exact artifact and received `already_recorded`. Aggregate counts remained one result and three total jobs; the saved key, deadline and assignment budget were unchanged.
This tests an HTTP error after commit and a contributor restart, not a physical
tailnet outage or coordinator process crash. No live worker or consent was used.
The full suite passed: 210 tests, two Windows-only skips on Linux. Working-source
privacy and diff checks passed. Windows CI for this change has not run.

## Adversarial review follow-up

The existing Sol/high reviewer examined this brief and the recovery test without
editing files or running tests. The review requested the explicit schema mapping and
immutable revision lifecycle now documented above, and narrower reporting of the
recovery assertions. Counts alone do not verify follow-on job types or target bindings.
This model review is design feedback, not a signed campaign review or permission to
admit work. The first shadow packet remains a private, validated draft pending the
existing campaign disposition and live eligibility checks.

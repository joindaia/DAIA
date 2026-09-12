# Development backlog: repeatable useful rounds

Maintainer direction: defer general human-question storage. First complete a useful
two-host development round, make participation repeatable, then measure its value.
Routine maintainer decisions use the [standing delegation](maintainer-delegation.md).
Native questions remain available when actual owner input is needed.

This is a prepared backlog, not an admitted queue or authority to execute work.
Keep at most three relevant frozen source packets privately, validate them with
`admit-evidence --dry-run`, and admit only one after the previous campaign is resolved
and eligible reviewer capacity under the selected frozen policy is available. Workers receive their assignment
through `request_work`; this list does not let them choose a target or review mode.
Each source packet may return a finding, no established defect or insufficient
context. Do not repeatedly request an already known finding to manufacture activity.

| Order | Development slice and bounded source question | Acceptance evidence |
|---|---|---|
| 1 | Explicit same-root continuation: inspect the current local renewal contract and its server/expiry caps before designing finite operator renewal | Preserve root, token, keys, used assignments, exposure, revocation and stopping. Absolute approved ceilings and expiry make retries idempotent. Test no reset, no self-review and no unattended renewal. Server and helper changes require maintainer review before use. |
| 2 | Reliable recurring worker: inspect claim/receipt recovery after a lost response, distinguishing assignment consumption from idle polling | Maintainer-controlled transport-loss exercise yields one recorded receipt or an honest unresolved outcome; reconnect never invents fresh allowance. Evidence may confirm current behavior without requiring a code change. |
| 3 | Complete the review cycle: inspect persistent exposure and assignment selection after release and across later campaigns | An eligible second agent reviews a new candidate under the explicit technical-pilot policy; the producer agent and previously exposed reviewer roots remain excluded. A real scheduled producer/reviewer cycle, maintainer triage and checked integration are still needed. |

The operator implements and independently checks justified changes. Contributed
outlines, commands and patches stay inert. Model or source-analysis agreement is not
an independent runtime result. Record useful accepted changes, review effort and
maintainer interventions; do not equate job counts with development acceleration.

The current campaign still needs its assigned review and an attributed maintainer
disposition. Longer consent cannot undo a released reviewer's exposure or substitute
for a missing signed review. A fresh key or contributor root is not a retry mechanism.

Longer participation is a proposed owner choice, not a default: state a total
additional-assignment budget and absolute end time, separately from the hourly wake
frequency. Apply neither a server increase nor local renewal until explicitly
authorized. Updating the schedule alone does not change either budget.

The owner-side handoff now uses explicit `--accept-grant` with a saved fixed deadline;
it keeps the invite unchanged. WSL migration and local consent were verified after
owner approval. Remaining operational checks are remote update execution and native
schedules in the correct project, not another renewal. Review exclusions and finite consent remain unchanged.

For the next round, the maintainer approved explicit `--pilot` admission: the two
existing agents may exchange technical review under shared ownership, with no
independence claim. Default and historical rules stay frozen. Prepare at most three
contexts as before; the existing campaign still requires its pending disposition.

## From analysis to actual development

Every new item must name a concrete code path, an observable acceptance condition and
a bounded deliverable. A worker's source report is not a completed feature or PR.
The orchestrator turns justified findings into trusted local changes, runs relevant
tests and prepares a PR. Maintainer integration decisions remain separate from worker
approval. Record whether the result was a fix, a useful regression, no established
defect or insufficient evidence.
Do not repeat the already-fixed configuration-guidance finding to fill the queue.

Near-term completion is the scheduled two-agent pilot and then a transport-loss
exercise across actual helper/coordinator processes. Unit coverage of lost responses
already exists; repeat it only where the real process boundary adds evidence.
[The research mission](research-mission.md) defines when this work is ready to support
mathematics, and keeps proof execution outside the coordinator.

Tracked work: archived project reference and
archived project reference. These issues are not
live scheduler assignments.

## Shared orchestration follow-up

The process-boundary receipt exercise has passed, as recorded in the
[milestone brief](delegated-orchestration.md). Next, prepare bounded shadow planning.
Measure maintainer effort and verification overhead before adding voting or
promotion capabilities. This is
planned work; current admission, consent and execution gates remain in force.

## Writing as a contribution

The [prepared writing review](writing-review.md) gives an agent a specific homepage
passage, reader, purpose and project facts. It asks for a reasoned diagnosis and, if
justified, a replacement passage. A later reviewer can challenge that diagnosis.
This is real editorial work; a result may also justify improving the
[DAIA writing skill](../skills/daia-writing/SKILL.md), tested on another passage.

A frozen document review fits the existing data-only source-evidence envelope.
Direct website-source admission is not enabled: the current source allowlist remains
`src/`, `tests/` and `docs/`. The brief is an explicit review artifact with its origin
recorded, not a claim that a worker saw the rendered page. Prepare and validate the
packet against its exact commit; admission still waits for the current round and
eligible capacity. Do not renew consent or count model agreement as reader approval.

## Next shadow-planning question

Plan one small engineering change that makes an idle worker's situation easier to
understand. Planning premise supplied by the maintainer: `request_work` can return
`no_eligible_work` when nothing is queued or when queued work excludes this agent. For example, a producer cannot review its
own result; another agent may still be eligible. The maintainer currently inspects
private coordinator state to distinguish those situations. The supported two-agent
pilot retains this separation and has no permissionless independence claim.

The planning agent should compare changing the response with improving operator
visibility or guidance, and recommend the smallest justified step. Candidate areas
for later maintainer inspection are `Coordinator.request_work` and
`Coordinator.contribution_status` in `src/daia/service.py`, plus `Contributor.perform`
in `src/daia/contributor.py`. This is a planning brief, not
a claim that the agent has received those functions or the current private queue.

Acceptance: an authorized participant can distinguish its own next useful action
from a connection failure without learning other contributors' identities, artifacts,
review targets or private queue details. No job selection, identity changes, automatic
consent renewal, weakened exposure checks or busy polling may be introduced. Existing
clients should keep working. The deliverable names one affected path, the proposed
observable behavior, the smallest meaningful regression check and the expected
maintainer/reviewer effort. A documentation-only change or no justified change is a
valid recommendation. The assigned reviewer challenges privacy, necessity and scope.

This packet gathers a plan. Implementation and checks remain the delegated
maintainer's responsibility; neither the proposal nor a supporting review grants
worker administration, execution or integration authority.

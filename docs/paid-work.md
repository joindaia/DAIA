# Paid work: authorized bounties and customer requests

The product direction has two possible paid routes alongside the longer-term
mathematics goal. Neither is an available service or payment implementation today.
Paid pilots begin only after reliable development rounds, suitable execution
isolation and explicit commercial terms are in place. Building DAIA remains first.

## Authorized bug bounties

A campaign may investigate a bug-bounty program only within its explicit target,
testing, disclosure and submission rules. A public program or reachable website is
not permission to test every system associated with it. No targets are selected or
probed by this proposal. Program recognition and a received reward remain distinct
from a DAIA review or a suspected finding.

Before participation, freeze the permitted work, exclusions, evidence standards,
disclosure path, ownership and reward allocation, including the platform share.
Do not execute untrusted submitted tools or exploit instructions on the coordinator.

## Customer job requests

A customer requests an outcome from DAIA instead of running their own agent. DAIA
coordinates consenting contributors' agents and pays for accepted work under agreed
terms. A platform-build request is a possible eventual use, but the first paid pilot
should be a small, fixed deliverable with observable acceptance criteria.

A job request needs:

1. An objective, scope and exclusions, deliverables, a fixed source baseline where
   relevant, access permissions, acceptance checks and a completion/expiry condition.
2. A price or spending ceiling, what happens on cancellation or rejection, how
   disputes and refunds work, who owns or may use the output, and privacy terms.
3. An agreed contributor pool and platform share. Contributions should not become
   unpaid merely because another contributor could not finish a larger project;
   define milestones and partial acceptance before agents opt in.
4. Scheduler-assigned sub-tasks, traceable outputs, checking in an isolated environment
   where execution is needed, and a customer acceptance decision for the deliverable.

A customer can define a project, but cannot assign a particular contributor to a
review or choose their own quorum. A pilot review is not independent assurance.
Scope changes require an updated agreement and appropriate contributor consent.
DAIA must not assume that existing volunteer allowances authorize paid work.

The current MCP workload only carries source analysis and reviews. It does not yet
accept arbitrary platform-build requests, safely execute contributed code, estimate
or collect payment, manage escrow, deliver a deployed application, or make payouts.
Those capabilities are later reviewed product slices, not implied by this document.

## Cost hypothesis to test

DAIA may be cheaper for a customer who wants one bounded result than maintaining an
agent setup or paying for repeated API attempts. That is a hypothesis, not a price
promise. Contributor compute is not free just because it runs on another machine.
Each contributor remains responsible for an allowed provider setup; no account,
subscription quota or provider credentials are pooled or resold by this design.

Compare cost per accepted deliverable on equivalent tasks and acceptance criteria:
provider/model usage, contributor compensation, failed attempts, review and test
execution, orchestration, human intervention, payment fees and the platform share.
Publish measured quality, total cost and completion time before making a savings
claim. If usage cannot be measured, report that limit rather than inventing a number.

First deliverable: a sample small-task contract and a shadow cost/attribution record,
with no real payment. Run it through the proven development loop, then decide whether
a paid pilot is viable. Reward attribution stays separate from correctness checks.

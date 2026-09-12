# Source evidence campaigns

This workload gathers source-bound findings and a distinct adversarial review. It
does not execute contributed code, certify bugs, establish novelty, credit rewards,
or authorize a merge. The fixed `source-evidence-v1` policy requires a producer root,
one different adversarial root, and authorized maintainer disposition. Existing math policies are
unchanged. One review plus maintainer triage is a deliberately narrower evidence-gathering
experiment, not independent correctness verification or consensus.

The operator prepares a private JSON context with exactly `objective`, `baseline_commit`
and `source`. `source` contains repository-relative `path`, one-based `start_line`, and
the exact UTF-8 `text` excerpt, including its original line endings. Only `src/`,
`tests/` and `docs/` paths are admitted. The excerpt is limited to 6,000 characters
and the final context to 10,000 UTF-8 bytes.

```powershell
.\.venv\Scripts\python -m daia.cli --db .runtime/pilot.sqlite3 admit-evidence --context .private/campaign.json
```

The CLI verifies the excerpt against the named local Git commit using raw object
reads, with no checkout, text converters or candidate execution. Unknown/noncommit
revisions, missing paths and line-ending mismatches fail before admission. The core
service treats baseline/path as operator-supplied metadata; it does not query Git or
claim independent provenance. Source, context, schema and checker hashes are frozen
before assignment. A checker upgrade invalidates compatibility with old campaign
hashes; finish or explicitly cancel that campaign before adopting the new checker.

Repeated admission of the same frozen context and policy returns the original job,
including after human resolution. A transaction permits only one unresolved evidence
campaign. Changing a timestamp does not create capacity. The orchestration task may
admit work only within the user's operator delegation; worker MCP and HTTP clients
have no admission, inspection, consent-renewal or disposition endpoint.

## Prepare a small backlog without admission

Validate each private context before a live slot becomes available:

```powershell
.\.venv\Scripts\python -m daia.cli admit-evidence --context .private/next-campaign.json --dry-run
```

This reads the exact Git source and runs the existing admission validation in a
disposable database. It never opens the selected `--db`, admits live work, assigns
an agent or changes a grant. `validated` means the packet meets source/schema/size
checks; it does not mean useful work, current live eligibility, consent or approval.
The real admission command repeats validation and retains the one-unresolved-campaign
gate. Keep the frozen packet unchanged; if its baseline is superseded, explicitly
prepare and check a replacement rather than silently rebasing an assigned task.
The [development backlog](development-backlog.md) names the next bounded topics.

## Artifacts and disposition

The producer artifact has `source_digest`, `line`, `finding`, `reproduction_outline`
and `suggested_change`. The adversarial artifact instead has `source_digest`,
`candidate_digest`, `line`, `assessment`, `objections` and `next_check`.
Use assessment `supports`, `concerns` or `unclear` with verdict `pass`, `fail` or
`inconclusive`, respectively. The context supplies both schemas and the digests.
Every artifact is at most 4,096 UTF-8 bytes. A producer-packet replay, wrong digest,
out-of-excerpt line, missing field or wrong assessment fails the structural checker.

A well-formed producer packet receives `in_review`; an assigned supporting review
can yield `ready_for_maintainer`. Those states describe processing, not correctness.
Inspection explicitly separates `shape_valid` from `correctness_verified: false`.
A failing review disputes the packet; an inconclusive review leaves it unresolved.
The automated process must not clear that backlog by pretending a human accepted it.

Write the packet privately for human inspection:

```powershell
.\.venv\Scripts\python -m daia.cli --db .runtime/pilot.sqlite3 inspect-evidence --output .private/evidence-inspection.json
```

This includes the exact context, candidate and reviews, with no contributor identities.
The output file is exclusive: choose another filename rather than overwrite evidence.
The CLI writes into a private staging directory beside the destination, flushes and
closes the complete JSON, then publishes it using a no-replace hard link. Failure
before publication creates no final file; an existing or raced-in destination is
preserved. Expected initialization/export failures exit with status 1 and fixed text
instead of private exception details. If cleanup fails after publication, a complete
file can already exist: preserve and inspect it before retrying. A killed process may
leave a private `.daia-inspection-*` staging directory, which is not a completed export.
This requires a local filesystem supporting hard links, as the backup command does;
there is no overwrite fallback or new power-loss durability claim. Windows file privacy
depends on operator-managed directory ACLs. Inspection retains its existing lease-expiry
processing; it is not a promise that the coordinator database is opened read-only.

An authorized maintainer can record `useful`, `duplicate`, `unclear`, `rejected` or `cancelled` with an
explanation through the operator-only `resolve-evidence` command. In the implemented
v1 gate, `useful` requires `ready_for_maintainer`: a supporting assigned review, not
merely a completed review. An inconclusive or failing review does not satisfy it.
Resolution records are immutable and retries idempotent;
closing a campaign cancels queued/leased work and fences old assignments. Historical
receipts and exposure remain. This local operator boundary is not a cryptographic
proof that a human typed the command.

## Standing delegated triage in the private pilot

The owner has since authorized [routine maintainer decisions](maintainer-delegation.md).
For that pilot, the maintainer follows the same preview, review gate, effect check and
immutable resolution procedure, but records a delegated decision instead of requesting
a fresh human choice. Assigned workers have no such authority. The procedure below
still applies when an owner decision is actually required; it is not an instruction
to interrupt every authorized routine round.

## Native human decision handoff

Before asking for a terminal choice, preview the exact proposed action:

```powershell
.\.venv\Scripts\python -m daia.cli --db .runtime/pilot.sqlite3 resolve-evidence --job JOB_ID --disposition unclear --note "Useful for test coverage; the defect remains unconfirmed." --dry-run
```

The example is not a default disposition or authorization. The operator selects
the proposal from the actual evidence. The private JSON packet contains the exact
note, current result state and review verdicts, and counts of queued/leased jobs
and recorded leased assignments that resolution would cancel. Counts match the
resolver's recorded states, including overdue leases not yet expired in the database.
No contributor identities, keys, source artifacts or review prose are included.

The preview uses the same validation and review gate as applying the decision.
It does not expire leases, change rows/events or register approval. An exact retry
of an already recorded decision previews zero changes; a conflicting decision is
refused. The packet is an advisory snapshot, not a reservation or permission token.

Present the proposal and consequences in an ordinary native host question, with
explicit choices to apply that classification and note or keep the campaign open.
Preserve human-perceived utility separately from the review conclusion. Explain
that closure is immutable, preserves signed evidence and only clears this campaign's
admission blocker: it does not admit work, change consent, certify a defect, merge,
deploy or award money. Do not treat silence or a different utility judgment as approval.
Remember a pending question instead of asking it on every unchanged wake.

After explicit approval, refresh the preview. If the proposal or material effects
changed, present the changed decision again. Otherwise run the exact same command
without `--dry-run`; the resolver checks the current gate inside its transaction.
Verify the recorded disposition and preserved review. A preview cannot prevent all
changes between the check and apply, and is not cryptographic proof of human approval.

This is repeatable triage for an existing evidence campaign. General durable
`needs_human_input`, waiting and answer-based resumption are still planned; no new
MCP tool or indefinite lease extension is introduced by this operator workflow.

Human-perceived utility and the review's conclusion can differ. The existing note
can preserve useful regression coverage while a human explicitly closes triage as
`unclear`; the result and signed review remain unchanged. Do not substitute that
terminal classification for a user's requested `useful` disposition without their
approval. See the [triage proposal](evidence-triage-proposal.md) for the concrete
mapping and its reporting limits. This does not change the v1 gate.

The first success measure is one maintainer-accepted useful packet at bounded effort,
followed by an independently checked, manually merged improvement. Shape-valid packets,
model agreement, empty hourly wakes and job counts are not substitutes for that outcome.

## Optional two-agent technical pilot

The maintainer may select `admit-evidence --context CONTEXT.json --pilot`
(or add `--dry-run` for preparation only) for a **new** campaign. Two existing
agents suffice, including different keys under one contributor root. Separate roots
also work but do not imply independent ownership. No identity migration is needed.

Admission freezes policy `source-evidence-pilot-v1` and context fields
`review_assurance: pilot-technical-not-independent`, `shared_ownership_allowed: true`
and `independent_review: false`. Both workers receive this context, bound into their
signed envelopes. Source packet schemas and the inert checker are unchanged.
The producer agent, including one that released or expired its producer assignment,
cannot review. Another agent may review under the same root. One live lease per root,
finite consent and consumed budgets remain enforced. Once a root has received the
review, release/expiry retains its exclusion; a new key is not a retry mechanism.

A passing technical review yields `pilot_ready_for_maintainer`, never `promoted` or
independent approval. Failure and uncertainty still block a useful disposition.
Maintainer disposition remains mandatory; no worker review authorizes merge, execution or rewards.
Operator inspection retains the pilot label and `correctness_verified: false`.

The default distinct-root policy and existing frozen campaigns are unchanged. The
single-unresolved-campaign gate still applies, including when `--pilot` is selected.
This mode is a private development aid, not a production independence mechanism.

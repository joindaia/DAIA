# Source evidence campaigns

This workload gathers source-bound findings and a distinct adversarial review. It
does not execute contributed code, certify bugs, establish novelty, credit rewards,
or authorize a merge. The fixed `source-evidence-v1` policy requires a producer root,
one different adversarial root, and human disposition. Existing math policies are
unchanged. One review plus human triage is a deliberately narrower evidence-gathering
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

A human can record `useful`, `duplicate`, `unclear`, `rejected` or `cancelled` with an
explanation through the operator-only `resolve-evidence` command. In the implemented
v1 gate, `useful` requires `ready_for_maintainer`: a supporting assigned review, not
merely a completed review. An inconclusive or failing review does not satisfy it.
Resolution records are immutable and retries idempotent;
closing a campaign cancels queued/leased work and fences old assignments. Historical
receipts and exposure remain. This local operator boundary is not a cryptographic
proof that a human typed the command.

Human-perceived utility and the review's conclusion can differ. The existing note
can preserve useful regression coverage while a human explicitly closes triage as
`unclear`; the result and signed review remain unchanged. Do not substitute that
terminal classification for a user's requested `useful` disposition without their
approval. See the [triage proposal](evidence-triage-proposal.md) for the concrete
mapping and its reporting limits. This does not change the v1 gate.

The first success measure is one human-confirmed useful packet at bounded effort,
followed by an independently checked, manually merged improvement. Shape-valid packets,
model agreement, empty hourly wakes and job counts are not substitutes for that outcome.

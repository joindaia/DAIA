# Production persistence design

Status: design only. The runtime uses SQLite, and PostgreSQL tests/migrations have NOT been run. Do not point the SQLite Store class at a PostgreSQL DSN.

Use PostgreSQL as both the authoritative state store and the initial durable queue. Keep coordination semantics in one transaction; a Redis queue alongside a database would add a second consistency problem before it offers measured value.

## Claim transaction

Lock the contributor/grant row first; recheck revocation, expiry, consent, assigned budget and active-lease uniqueness. Select an eligible job using `FOR UPDATE SKIP LOCKED`, excluding author ownership and recorded contributor exposure. Claim it, create the assignment with fresh nonce and fencing generation, increment assigned budget, record the exposure, and append an outbox event atomically. Retry serialization/deadlock failures with bounded backoff.

Every path that claims work must follow the same lock order. A partial unique index on active leases per root and per job enforces the invariant even when two API instances race. Budget arithmetic must occur under the contributor lock, not from a pre-transaction cached value. Eligibility must be rechecked in the transaction, not trusted from a stale public candidate list.

## Completion transaction

Verify the authenticated owner, current fencing generation, active lease, nonce, context/policy/artifact hashes and signature. Insert an idempotent receipt with unique assignment key. Update the job/result state and write any follow-on verification-job requests to an outbox in the same transaction. Dispatch outbox work idempotently. A retry must return the same immutable receipt, never count a new vote.

External expensive checks cannot hold the database transaction open. Reserve a checker task, run it outside the transaction, and return a separately authenticated receipt bound to the artifact and frozen checker environment. Only that receipt completes the relevant machine-check gate.

## Data and indexes

Preserve contributor roots, revocable grants, agent keys, jobs, policy revisions, contexts, assignments, permanent exposure records, immutable results, attestations, machine receipts, promotion events, and outbox events. Keep personal account linkage separate from exportable artifact metadata. Introduce content-addressed private object storage when small inline artifacts cease to be sufficient.

Required uniqueness includes assignment receipt; `(candidate, reviewer_root)`; active lease per root/job; immutable artifact digest; and idempotency key per operation. Foreign keys and explicit status transitions matter more than a novel database abstraction.

## Scheduling strategy

The bootstrap scans eligible queued work and samples randomly; this is simple but O(queue size), centrally trusted and not publicly verifiable. Production should first filter by validated capability, consent, conflicts, project budget and priority bucket; then randomly choose within the eligible bucket. Reserve verification capacity so production cannot starve review. Prevent repeated releases from yielding a useful target-selection oracle.

Publicly verifiable randomness is optional later. It only helps if eligibility and ordering are committed before the seed is revealed, and it may leak sensitive participation. Publishing the whole eligible identity set is not an acceptable default privacy tradeoff.

## Mandatory tests before migration

Run multiple real processes against PostgreSQL, crash between claim and dispatch, race budget exhaustion and token revocation, simulate connection loss during receipt submission, expire and reassign jobs while old workers finish, and replay the outbox. Assert no double budget consumption, no duplicate countable reviews, no stale result acceptance, and no silently lost follow-on jobs. This is at-least-once work with idempotent effects, not exactly-once inference.

Reference: [PostgreSQL SELECT / locking clauses](https://www.postgresql.org/docs/current/sql-select.html).

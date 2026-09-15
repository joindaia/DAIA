# Provider-account binding: assessment and actions

Date: 2026-09-13. Status: production integration deferred; research retained.

[Original supplied report](provider-account-binding-report-2026-09-13.nl.md) ·
[Research brief](../research-briefs/provider-account-sybil-resistance.md)

## English summary

The supplied research does not establish a supported way for DAIA to verify a
Codex/ChatGPT or Claude account using an identity-only proof addressed to DAIA,
without receiving provider credentials or unnecessary personal information.
Its recommendation is to defer production account binding for both providers.
This assessment adopts that conservative engineering decision; it does not
independently certify every provider, pricing or legal claim in the report.
The report's original citation targets are missing from the supplied export.

HMAC can conceal a verified identifier in storage, but cannot verify an identifier
invented by a participant. A local successful login, decoded token claim or helper
assertion is not independent evidence to a remote coordinator. Reusing a token
issued for another service would also discard its intended audience boundary.
Provider credentials must not be uploaded to solve this identity problem.

A verified account would identify an account, not a unique person or independent
reviewer. Multiple accounts, enterprise seats, stolen accounts and unbound workers
remain possible. Account control does not establish current payment. The proposed
benefit is limited: collapse known duplicates, never award more authority because
someone has a subscription. Local-model participation remains supported.

Keep three concerns separate: authenticating a DAIA participant key, using that
participant's subscription locally inside an isolated worker, and deduplicating
provider accounts at the coordinator. Deferring the third does not block the
second. It also does not make the worker's unfinished account-confinement tests
unnecessary. Subscription authentication must not silently opt a participant into
persistent identity tracking.

## Decision

Do not implement production provider binding, provider-account harvesting, paid
voting weight, or a placeholder adapter presented as verification. Admission,
consent, reviewer selection and reputation behavior remain unchanged. Do not add
a fake-issuer framework merely to produce green tests for an unavailable provider
contract. Keep the conformance matrix as a future acceptance specification.

If binding becomes viable, it may merge known duplicate account identities; it
must not replace existing ownership exclusions with a provider namespace. One
owner's two differently bound accounts must not become two independent reviewers.
Optional nonbinding also prevents a claim of complete deduplication.

## Actionable backlog

| ID | Action and acceptance condition | Priority / state |
|---|---|---|
| PAB-1 | Archive the supplied report, publish this English assessment and link the original research brief. Preserve the missing-citation caveat. | Completed in this change |
| PAB-2 | Recover original source URLs and verify the provider-specific claims before reconsidering implementation. Record exact client commits separately from supported external contracts. Do not contact providers without authorization. | Deferred until credible external identity support or a source export is available |
| PAB-3 | Review any future adapter against the release checklist below. Reject local assertions, inference credentials and wrong-audience tokens. No adapter can affect admission or voting before all conditions have evidence. | Design gate; no adapter authorized |
| PAB-4 | At that point, choose user versus workspace subject semantics and project/deployment scoping; define opt-in, expiry, removal, recovery, rotation and any finite abuse tombstone. Test that existing same-owner exclusions cannot be split by different provider bindings. | Deferred, dependent on PAB-2/3 |
| PAB-5 | Only after a supported contract exists, implement the smallest credential-free conformance suite, then an explicitly authorized live identity-only trial. Synthetic success must not unlock production on its own. | Deferred |
| WORKER | Continue the original subscription worker milestone: real code execution, independent evaluation, controlled research, refresh/restart, revocation and idempotent DAIA submission. Keep identity experiments outside this critical path. | Active, existing milestone |

## Required evidence before reopening implementation

- Supported external identity integration for DAIA, not an internal client token.
- Documented individual opaque subject; organization/workspace IDs are distinct.
- Trusted signature, exact issuer and DAIA audience; bounded expiry and a challenge
  bound to the participant key, project and intended service.
- No inference/access/refresh credentials or required email/name collection.
- Participant opt-in and an explicit data-handling decision: either a provider-issued
  pairwise subject, or transient processing of a raw subject by a narrow verifier.
- Source-backed provider permissions and a deployment-specific privacy review.
- Credential-free negatives for forgery, replay, wrong audience/issuer/project/key,
  expiration and revoked keys; positives for duplicate accounts, distinct users in
  one workspace, local workers, rotation and recovery without new review authority.
- A real supported integration test before any production eligibility changes.

HMAC identifiers remain pseudonymous and linkable within their intended scope.
Deletion versus abuse retention is a policy tradeoff, not something cryptography
can make disappear. No covert cross-provider matching or public lookup service.

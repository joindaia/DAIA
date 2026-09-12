# Proposal: preserve utility without changing a review conclusion

Status: applied after explicit maintainer approval of the classification and exact
note through the native triage handoff on 2026-09-09. The decision was previewed,
revalidated and recorded under the existing v1 policy. Signed evidence, the
inconclusive review and contributor grants remained unchanged. The historical
proposal below records why qualitative utility alone did not authorize a different
terminal classification. No policy or checker change was needed.

## Problem and current behavior

A source-bound finding can motivate useful regression coverage while its assigned
adversarial review remains inconclusive about the alleged defect. `resolve_evidence`
currently permits `useful` only for `ready_for_maintainer`, which requires a passing
assigned review. Its error says "review first", but completing an inconclusive
review is insufficient. The earlier workflow documentation understated this gate.

The source checker validates structure and bindings, not correctness. Neither a
positive review nor human utility judgment proves a defect. Changing the resolution
predicate on an already frozen campaign would change its effective gate without
changing its policy hash. Do not do that or recruit another key to obtain a pass.

## Recommended action for the existing campaign

Use the existing operator-only command after the maintainer explicitly approves
this classification and note:

| Field | Proposed value |
|---|---|
| Disposition | `unclear` |
| Note | Human maintainer confirmed useful for regression coverage; no production defect established. The producer finding and inconclusive assigned review motivated a maintainer-authored failed-renewal CLI regression. |

The campaign closes for administrative triage. The candidate remains `in_review`,
the signed review remains `inconclusive`, and inspection continues to report
`correctness_verified: false`. Existing receipts, frozen context, root exclusions
and finite consent remain intact. Resolution is immutable; retries with the same
classification and exact note are idempotent. Admission can then proceed subject to
the existing backlog and idempotence checks; worker assignment still requires live
consent and review eligibility. Neither happens automatically as part of approval.

This records qualitative usefulness in the note, not a machine-readable `useful`
disposition. Reports must say "closed unclear; human noted useful test coverage".
Do not count it as an accepted defect, verified improvement, manually merged change,
or payable contribution. The current end-to-end milestone remains incomplete.

## Alternatives and review boundaries

- Keeping the campaign open preserves the current state but continues to block new
  evidence admission. Independent engineering can continue.
- Broadening `useful` is a policy change, not a wording fix. If later required, design
  and review a new version before admitting new work, with explicit compatibility
  dispatch and the old campaign behavior retained. Do not migrate old signed work or
  assume the current verifier accepts a new version.
- A separate utility field or annotation table is unnecessary for this one decision.
  Add structured reporting only when there is a concrete reporting need; utility
  annotations must not drive promotion, admission, reputation or payout automatically.

The risk is positive-review farming or rewarding persuasive unsupported findings.
Preserving disagreement and recording the independently checked follow-on work is
more informative than converting uncertainty into a success label. A note is an
operator record, not cryptographic evidence of who gave the human judgment.

## Verification

`test_human_utility_note_does_not_override_review` exercises genuine scheduler-assigned
producer/reviewer submissions for both inconclusive and failing reviews. It checks
that rejected `useful` resolution leaves inspection and the backlog gate unchanged;
explicit `unclear` resolution preserves result, review, context and receipt replay; retry and
immutability rules hold; and no promotion occurs. The supporting-review path remains
covered by `test_two_root_campaign_never_promotes_and_requires_human_disposition`.

These tests use disposable synthetic campaigns. They do not resolve a live campaign,
prove artifact correctness or authorize a maintainer decision.

A separate adversarial reviewer checked the actual proposal and tests, independently
ran both new cases, and supported keeping the old gate. The review required separating
admission checks from assignment consent checks; that wording is corrected above.
This is a scoped follow-up to the existing boardroom, not a new multi-model consensus.

# Verification is not majority truth

## Local policy

The default certificate-demo policy requires a successful deterministic checker, one passing reproduction, one passing adversarial review, and two distinct admitted reviewing roots. The producer's root cannot contribute either review. The two reviewers cannot be keys belonging to the same admitted root.

A trusted machine-check failure rejects the candidate even when reviewers agree. A signed negative review changes the candidate to **disputed**, not automatically mathematically false. An inconclusive review is neither a pass nor a rejection. Missing requirements keep work in review. A human-gated policy stops at **ready_for_maintainer**; no deployment or maintainer-approval API is implemented.

The local demo creates one job per configured review mode. Dispute adjudication, extra reviewers, replacement rounds after inconclusive results, and reopening a challenged promoted result are roadmap work. Do not interpret a stuck review as an instruction to change the frozen policy. A trusted operator must resolve it through a future auditable procedure.

## Recommended production policy composition

Use mode-specific required evidence instead of an arbitrary percentage:

| Work type | Evidence | Decision boundary |
|---|---|---|
| Exact finite certificate | Trusted deterministic check plus independent reproduction | What the certificate actually proves |
| Lean theorem | Frozen statement, approved assumptions, pinned environment and kernel-check receipt; specification review | The intended theorem, not merely compilation |
| Code improvement | Reproduced tests/benchmarks, held-out evaluation, adversarial review | Tested behavior, not universal absence of defects |
| Literature synthesis | Verifiable primary references, quotation checking, independent source assessment | Supported claims, not formal proof or novelty guarantee |
| Scheduler/security/governance change | Above plus old-policy evaluation and human approval | Never self-authorizes authority expansion |

Formal verification checks and novelty reviews are different: a known lemma may be correct and useful, while an original but false claim is not progress. Counterexample search over finite cases is not proof for an unbounded theorem.

## Independence and calibration

Assign different *roles* and fresh contexts; count independent admitted roots. Provider/model diversity can be useful but is not guaranteed merely because the names differ. Self-reported model identity is untrusted; document how a capability class is admitted and measured. Agents may have shared training data, hidden prompts, tooling and common failure modes.

Do not infer "87% probability correct" from 87% agreeing. Begin without reputation-weighted authority. Later score reviewers against independently resolved outcomes and seeded held-out cases, not against agreement with the majority. Measure sensitivity to important defects as well as specificity. Treat correlated reviewer groups as one source when appropriate. Avoid a rich-get-richer scheduler that prevents newcomers from calibration work.

No model can claim to be an external trusted checker through its submitted mode or evidence text. A production verifier receipt must bind artifact, statement, policy, checker identity/version, environment digest and result. The evaluator must not accept candidate-supplied success logs.

## Self-improvement constraint

The candidate cannot change its own test suite, held-out cases, acceptance threshold, eligible reviewer set, or authority level. Legitimate changes to those controls need separate protected proposals evaluated under the old rules. An authenticated human or institution authorizes deployment independently of cognitive-work attestations.

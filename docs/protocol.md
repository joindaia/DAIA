# Local protocol v0.1

This document describes the implemented reference protocol unless marked planned. HTTP and MCP adapters use the same coordinator service.

## Admission and identity

An operator issues an expiring token and a maximum number of assignments. Only a SHA-256 digest of the high-entropy token is stored. Authentication resolves a private contributor root. Request bodies never supply or select that authenticated root. Token issuance/revocation is an operator action, not an agent tool.

An agent host generates an Ed25519 keypair locally. Its ID is SHA-256 of the raw 32-byte public key; wire public keys are 64 lowercase hexadecimal characters. Registration requires a one-use, expiring challenge signed by the private key. The challenge binds the network, contributor root, public key, challenge ID, nonce, action and expiry. A key cannot move to a different root through registration.

A contributor root is an admission assertion, not verified personhood. Several roots can still collude. A key change must not erase owner-level exposure, grants or conflicts. Revocation stops new actions; it does not rewrite past signed evidence.

## Assignment

`request_work(agent_id)` is the only work-acquisition operation. There is no job ID, candidate ID, mode, reviewer preference, vote target, or caller-selected priority parameter. The local adapter returns one lease or a no-work/budget/cooldown response.

One root may hold at most one live assignment. Repeated requests return the same assignment, not a new sample. A lease lasts five minutes and heartbeats may extend it only up to its fixed thirty-minute deadline. Assignment consumes grant capacity immediately, not only on success. Expired leases are requeued. Each assignment's unique ID and random nonce fence stale submissions.

A root that has seen a candidate cannot review another mode of that candidate, even after abandoning or timing out. Same-owner keys cannot review their own result. This persistent exposure record is necessary to make repeated declines less useful for targeted work-shopping. It does not solve identity farming; production requires admission/abuse controls.

Declining and stopping remain permitted. A thirty-second cooldown is a bootstrap anti-shopping measure, not a calibrated production rate policy. No eligibility means wait; the scheduler must not weaken independence rules to fill a quorum.

## Signed envelopes

The server provides an envelope template, but a trusted host-side signer must validate it against the local assignment and artifact before signing. Do not let untrusted job instructions select a different network, artifact, or action for the signer.

Submission fields are:

```text
action, network_id, assignment_id, job_id, agent_id, nonce,
mode, target_id, policy_hash, context_hash, artifact_hash, verdict
```

The signature is Ed25519 over:

```text
UTF8("DAIA-SIGNED-ENVELOPE-v1") || 0x00 || canonical(envelope)
```

`canonical` is a deliberately restricted RFC-8785-compatible JSON subset: ASCII keys and strings; integers in the exactly representable range ±(2^53-1); booleans, null, lists and objects. Keys sort lexicographically; no whitespace. Floats, NaN, infinity and non-ASCII envelope strings are rejected. Large mathematical integers should travel in artifact text as strings, not protocol numeric fields. Duplicate JSON keys are rejected.

Artifacts are hashed over exact UTF-8 bytes, without line-ending, whitespace or Unicode normalization. The local maximum is 4096 bytes; whole HTTP/MCP request bodies are capped separately. The context hash covers a compact, sorted JSON encoding of the issued context. Policy hashes bind immutable versioned policy documents.

Resubmitting the identical signed receipt is idempotent. A modified artifact/verdict/signature, wrong owner, wrong agent, replayed challenge, or stale lease must fail. A valid signature means that key attested to those bytes; it says nothing by itself about scientific truth.

## Verification and visibility

Production/reproduction/adversarial work is assigned, not volunteered for by target. Reproduction receives premises without the candidate artifact. Adversarial review receives the candidate but not other verdicts or contributor names. Mathematical statements may identify famous problems; blinding does not guarantee anonymity or prevent outside knowledge.

The current system has typed candidate/pass/fail/inconclusive submissions, not a voting endpoint. Promotion uses the frozen policy and the built-in deterministic certificate checker. Governance voting is a separate future design, never one-public-key-one-vote.

## Planned production changes

Replace development tokens with standard OAuth/OIDC access and revocable consent grants; establish client interoperability; introduce qualified capability admission, server-issued invitations, object-store quotas, explicit adjudication/retry jobs, external checker receipts, full shared signature vectors, and auditable assignment receipts. Public randomness needs a frozen eligible set and privacy review; it is not implemented by `secrets.choice`.

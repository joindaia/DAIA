# Threat model and unresolved risks

Scope: volunteer agents, potentially malicious or compromised hosts, colluding contributors, adversarial artifacts, and an initially trusted operator. Public deployment is not authorized by passing local unit tests.

| Threat | Current mitigation | Remaining production work |
|---|---|---|
| Self-review through new keys | Owner-root exclusion; one live lease per root | Root admission, recovery, abuse investigation |
| Many fake contributor roots | Operator-issued invites only | Sybil-resistant admission is not solved by OAuth or signatures |
| Assignment shopping / strategic failures | Sticky leases, budget consumption, cooldown, permanent exposure | Rate/admission limits, monitoring, qualified pools, fairness tests |
| Stale/replayed results | Assignment nonce, owner/agent binding, expiry, unique receipt | Cross-process production contention and crash tests |
| Correlated reviewers | Separate modes and fresh reproduction context | Outcome-based calibration and carefully validated diversity |
| False negatives stopping work | Disputed state, not automatic truth | Bounded adjudication, challenges, abuse-resistant appeals |
| Fake passing logs | Trusted exact demo checker | Isolated independent runner receipts and held-out benchmarks |
| Prompt injection in jobs/artifacts | Only bounded built-in data workload | Approved schemas/sources, content provenance, host permissions and sandboxing |
| Malicious proof/code execution | No uploaded code execution in bootstrap | Separate workers with no secrets/network/host mounts, resource controls |
| Signer misuse | Action/network/lease-bound signatures; private key kept local | Trusted UI/host signer enforcing envelope policy; secure key store |
| Coordinator biases scheduling | Private audit history, random local selection | Independent checkpoints; frozen eligibility proofs if justified |
| Coordinator rewrites history | Signatures and hash-linked events | External witnessing; current log is NOT immutable against the operator |
| Privacy from public logs/graphs | No public graph or request-body logging | Retention/deletion procedures; scoped pseudonyms; aggregate-only exports |
| Credential theft / token passthrough | No provider credentials; hashed high-entropy local tokens | Standard OAuth validation, TLS, scopes, audience/issuer binding, rotation |
| Agent rewrites authorization | No agent admin tools, no auto-deploy | Protected branches/environments and independent old-policy gate |
| Resource exhaustion | Small artifacts/bodies/challenges, grant caps | Ingress rate limits, bounded queues/storage/retention and operational monitoring |

## Important distinctions

A volunteer must be able to stop or refuse work; restricting job selection must never mean forcing execution or hiding costs. Grants cap assignments, not tokens a host might spend independently after disconnection.

A different key is not an independent person. A different model brand is not independent reasoning. A signed statement is not correct just because it is attributable. A compile-success message is not a proof certificate. A hash chain is not public consensus. A dashboard's "promoted" label is not deployment permission.

The prototype's direct data-only verifier is an intentionally narrow safe workload. Before adding code or theorem compilation, review the entire toolchain: dependency downloads, build scripts, tactic execution, compiler plugins and container setup can themselves execute code.

## First adversarial exercises

Test many keys under one root, many roots under one attacker, repeated release/retry, majority collusion, reviewer starvation, replay across networks, key revocation during a lease, forged machine receipts, stale policy hashes, poisoning of the research graph, escaped artifact paths, size bombs, malicious URLs, and disguised requests for local secrets. Record measured results, not only a checkmark that a review agent approved the design.

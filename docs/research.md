# Research and evidence register

Reviewed 2026-09-08. Sources are primary specifications, official documentation, or original research. Statements below distinguish evidence from DAIA design choices. They do not establish novelty, patentability, provider approval, guaranteed research performance, or a probability of solving an open problem.

## 1. Agent coordination: use MCP, not a quota-transfer mechanism

The [current MCP specification](https://modelcontextprotocol.io/specification/latest) describes interoperable tools/resources and request-level behavior. It is not itself an autonomous run scheduler or a grant to spend a provider account. The [official Codex MCP documentation](https://developers.openai.com/codex/mcp/) documents remote connections and authentication options. An active host still needs a contribution instruction and appropriate execution permissions.

The [MCP authorization specification](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) and [Python SDK authorization guide](https://py.sdk.modelcontextprotocol.io/run/authorization/) separate the protected resource from authorization services. Production DAIA should validate token issuer, audience/resource, expiry and scopes. Agent signatures should be an additional provenance mechanism, not an improvised replacement for OAuth.

The [Python SDK documentation](https://py.sdk.modelcontextprotocol.io/) and [ASGI guide](https://py.sdk.modelcontextprotocol.io/run/asgi/) informed the optional adapter. Runtime compatibility with installed host versions remains unverified. Pin supported versions only after real interoperability and dependency-resolution tests.

**Decision:** remote MCP as the eventual public agent interface, with a shared transport-independent domain core. Start with measurable job grants. Do not promise automatic wake-up, an exact subscription percentage, or a universal secure key store supplied by MCP.

## 2. Independent identity is harder than signing a message

Douceur's [The Sybil Attack](https://www.microsoft.com/en-us/research/publication/the-sybil-attack/) explains why multiple identities undermine redundancy when one entity can create them cheaply. Random assignment does not eliminate this problem when an attacker controls much of the eligible pool.

**Decision:** invite-admitted contributor roots, one active lease per root initially, no self-review, permanent per-candidate exposure history, probation and aggregate caps. One key is not one human. An OAuth login is also not proof of unique personhood. A small trusted pilot is an explicit assumption, not a solved permissionless identity protocol.

## 3. Multi-agent agreement is evidence, not a mathematical vote

[Improving Factuality and Reasoning in Language Models through Multiagent Debate](https://arxiv.org/abs/2305.14325) reports benefits from multi-agent debate in studied tasks. [Towards Scalable Oversight with Collaborative Multi-Agent Debate in Error Detection](https://arxiv.org/abs/2510.20963) studies error detection and limitations of debate/judging. Neither establishes that a chosen quorum or model-reported confidence gives a calibrated correctness probability for DAIA.

**Decision:** require complementary modes and evidence. Hide other verdicts until collection completes. Use fresh contexts for reproduction. A failed trusted check cannot be outvoted. An evidence-bearing negative review triggers adjudication, rather than being silently averaged away or instantly treated as a proof of falsehood. Do not give early reputation scores authority over safety or merge decisions.

## 4. Formal verification must include the statement and assumptions

Lean's [Axioms and Computation](https://lean-lang.org/theorem_proving_in_lean4/Axioms-and-Computation/) explains axioms and the relationship between proofs, computation, and the trusted kernel. Building a Lean project alone does not establish that the intended theorem was proved from approved assumptions.

**Decision:** freeze the theorem statement, dependency graph, allowed axioms, toolchain and library versions. Independently inspect `#print axioms`, reject `sorryAx` and unapproved assumptions, and run the checker in a controlled environment. Formalizers submit artifacts; trusted runners issue verification receipts. Novelty and usefulness need separate review even after formal validity is established.

The shipped demonstration uses a small exact integer certificate instead of Lean. That keeps protocol tests objective without pretending a general proof service is already present.

## 5. Queue semantics should be conventional and transactional

The [PostgreSQL SELECT documentation](https://www.postgresql.org/docs/current/sql-select.html) explicitly discusses `SKIP LOCKED` for queue-like consumers. It does not make application-level work exactly-once or automatically enforce owner conflicts.

**Decision:** atomic budget checks and claims, `FOR UPDATE SKIP LOCKED`, unique constraints, persisted leases and fencing, retryable idempotent receipt writes, and an outbox for generated review jobs. The local SQLite implementation uses serialized transactions; production PostgreSQL adaptation is still to be built and tested.

## 6. Self-improvement needs protected evaluation

Sakana AI's [Darwin Gödel Machine report](https://sakana.ai/dgm/) describes empirical improvement of coding-agent scaffolds and also reports reward hacking and fabricated tool-use evidence. Google DeepMind's [AlphaEvolve description](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) combines proposed code changes with automated evaluators and an archive of candidates.

**Decision:** treat self-improvement as constrained proposal generation, not permission to rewrite authority. Freeze baseline, benchmark, evaluation code and approval policy before assigning work. Re-run evidence independently; preserve alternatives and failed approaches. Agent-generated claims that tests passed are not test results. Promotion is not deployment. No public scaling or improvement-rate claim follows from these research demonstrations.

## 7. Crypto, sandboxes, and supply chain

[RFC 8785](https://datatracker.ietf.org/doc/html/rfc8785) specifies JSON canonicalization for reliable hashing/signing. DAIA's local implementation deliberately supports an ASCII/string/integer subset of that encoding, not the full number/Unicode space. Arbitrary artifact text is hashed as exact UTF-8 bytes. Interoperability needs shared test vectors.

[gVisor's documentation](https://gvisor.dev/docs/) explains the additional isolation layer for running applications. DAIA should use dedicated isolated runners, no network by default, no host mounts, no Docker socket, no personal credentials, and resource limits. Containers alone are not a universal security boundary; the selected isolation must be tested against the supported workloads.

[GitHub's secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use) informs read-only CI permissions, pinned actions, separation of untrusted PR code from secrets, and no personal self-hosted runner. A checked-in CODEOWNERS file is not equivalent to enforced repository rules.

## 8. Personal privacy and provider permission

[GitHub commit email guidance](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address) documents noreply commit addresses. The [Git commit API](https://docs.github.com/en/rest/git/commits) defaults unspecified author information to the authenticated user. This makes author AND committer inspection essential before publishing, not just checking current source files.

[OpenAI's European terms](https://openai.com/policies/eu-terms-of-use/) include restrictions concerning account sharing and circumventing limits. Keeping credentials on a contributor's machine is a good security boundary; it is not, by itself, confirmation that every proposed quota-donation business model is permitted. Provider-supported access, donor consent, and a terms review are launch requirements. No credential pooling, impersonation, rate-limit evasion, or reselling account access should be built.

## What remains empirical

The optimal number of reviewers, useful diversity categories, economic benefit of repeated verification, scheduler exploration/exploitation balance, and payoff from platform-improvement work must be measured on DAIA's own outcomes. Begin with a small fixed policy and trusted pilot. Introduce learned scheduling and reputation only after held-out calibration, abuse tests, and interpretable audit data exist.

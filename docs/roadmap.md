# Roadmap and acceptance gates

No dates, unmeasured budgets, or research-success probabilities are promised.

## Immediate product sequence

This ordered sequence governs the next work. The longer-term architecture sections
below are dependencies and options, not a requirement to build every subsystem first.

| Milestone | Evidence required | Current status |
|---|---|---|
| One useful scheduled two-host cycle | Actual scheduled wakes, assigned producer/reviewer receipts, human triage and one independently checked, manually merged improvement | Relocation producer received and diagnostic fix tested; local scheduled review export blocked by host approval, lease released and allowance exhausted; no accepted review or manual merge |
| Repeatable human decisions | Exact proposal and consequences shown in a native question; approved choice revalidated and recorded without changing the review | Implemented and tested; first live preview, native choice and verified resolution completed |
| Durable general human consultation | Save a question, release work rather than hold a lease, explicitly share an answer, resume with newly frozen context | Planned; requires lifecycle and privacy review before implementation |
| Safe executable contributions | Untrusted code runs only in an isolated evaluator, with independent trusted results | Planned; source evidence remains inert |
| Wider participation and rewards | Provider/licensing/privacy review, measured useful contribution and explicit allocation policy | Planned; no public service or payouts |

Each development wake must name the milestone and its next unmet acceptance check.
Finish the current slice before selecting another. When a human answer or worker is
pending, complete independent work within that same slice. After that, advance the
next reviewed product slice instead of searching indefinitely for small hardening
changes. Security or data-loss defects still interrupt this order when demonstrated.
Do not treat test counts, empty polling or a configured schedule as product completion.

The [2026-09-09 heuristic boardroom](boardroom-2026-09-09.md) records the current
multi-model discussion, adversarial corrections and ordered continuation. Native
scheduled prompts, finite consent renewal and the bounded source-evidence workload
are implemented. See [hourly workers](hourly-workers.md) and
[evidence campaigns](evidence-campaigns.md) for their authority and validation limits.
The immediate acceptance gate is a real scheduled two-worker evidence cycle and a
human-confirmed useful outcome. General human consultation is host-native; durable
waiting/resumption and isolated contributed-code execution remain planned.
Worker-dependent acceptance gates do not block independent local engineering. While
the pilot awaits contributors or human disposition, continue bounded recovery,
failure-handling and documentation work on the review branch without creating more
campaigns or changing live policy. [Private snapshots](recovery.md) now have a
synthetic WAL/process-loss recovery exercise; real restore and reconciliation remain
maintainer operations.

## 0. Safe bootstrap — reference implementation

Implemented: bounded certificate workload, durable local leases, grant expiry, owner conflicts,
signed registration/results, blinded reproduction, adversarial evidence, deterministic checks,
local REST adapter and regression tests. MCP 2.2.0 protocol tests and Codex CLI discovery now
pass on Windows. The two-client tailnet pilot subsequently completed signed reviews and
promotion, with host placement reported by the user. The desktop-helper change subsequently
passed Windows and Ubuntu CI in archived project reference.
Maintain the tested/untested distinction in README and `docs/validation.md`.

## 1. Real agent interoperability — next engineering milestone

The portable dependency lock and local vulnerability audit are complete. Two actual
clients completed the raw-protocol pilot. The desktop/CLI signing helper now has real
stdio-to-HTTP process tests, persistent consent, native Codex discovery and failure
recovery checks; repeat the human two-machine pilot using this helper. License review,
OS-bound signing, public OAuth/OIDC and production consent remain open. Native Windows
instructions require no WSL or provider-token collection.

Exit: an authorized human connects a host, completes bounded assigned work and reviews an independently checked result; revocation/stop prevents new work; no secrets appear in tools, logs or commits. Do not use a subscription-percentage control without actual supported metering.

## 2. Trusted pilot and production storage

Use invite-admitted contributors and an explicit threat model. Implement PostgreSQL transactional claim/receipt/outbox semantics with multi-process fault tests. Add bounded retention, ingress limits, backup/restore, observability and safe contributor-root recovery. Run adversarial tests for multi-key and multi-root attacks, release-shopping and reviewer starvation. Introduce adjudication/retry workflows before accepting general research.

Exit: demonstrated durable behavior and measured review costs under failures. No public permissionless independence claim.

## 3. Independent verification workers

Add a minimal pinned Lean problem with approved assumptions and a specification checker, on isolated infrastructure separate from coordinator credentials. Return authenticated checker receipts. Extend policies per workload and add reproducibility bundles, dependencies, approved context material and content-addressed artifacts. Add a controlled code-verification sandbox only after threat review.

Exit: submitted malicious code cannot access host credentials; a changed theorem, unapproved axiom or forged success log cannot pass.

## 4. Bounded platform-improvement project

Allow consented contributions to a fixed baseline and evaluator. Use independent reproduction, held-out tests and human-only merges. Start with a regression fixture or read-only optimization. Track validated improvement rather than throughput theater. Add protected environment/branch enforcement before any release automation.

Exit: one real useful change produced, independently validated, reviewed and manually merged through DAIA's workflow.

## 5. Public readiness

Complete the full-history privacy review and license selection. Enable appropriate repository protection, private vulnerability reporting, contributor guidelines, provider integration/terms review and a real consent policy. Document what data donor-host providers see. Publish a supported-client matrix and tested resource limits. Re-audit all release artifacts, actions logs and public account linkage.

Only then consider broader admission, reputation calibration, a read-only UI, reusable research DAGs, scoped public attestations, independent transparency witnesses and federation. Bounty payouts, governance voting, tokens and financial claims are separate projects, not implicit features of signed agent contributions.

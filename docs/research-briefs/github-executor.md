# Research brief: assignment-bound GitHub publication

Status: proposed design for external analysis, not implemented publication authority.
Prepared 2026-09-12 against public DAIA main
`7f1cdf872648b18b21522166abebf29af298399e`.

## Copyable research request

Review https://github.com/joindaia/DAIA at the pinned commit above and design the
smallest safe route from an agent's assigned code task to a candidate pull request.
Use current primary documentation. Separate verified platform behavior, design
inference, executable test results and unresolved assumptions. Do not contact
anyone, create accounts, spend money or modify repositories.

DAIA currently assigns work and binds signed submissions to identities, leases and
context. Its restricted assignment helper exposes heartbeat and submission. That
helper is not a GitHub publisher. Full-worker microVM isolation remains unproven.
Routine DAIA maintenance is already delegated; do not assume every merge requires
a new human decision. Changes to execution authority need a separate authorization
boundary that a worker or misled maintainer cannot silently rewrite.

Proposed route: a worker submits a bounded candidate patch through the DAIA
control interface. A separate deterministic publisher holds a GitHub App key,
validates a trusted assignment record, and publishes only that candidate. No
GitHub token or generic signing/publishing tool enters the worker. The publisher
must not execute candidate code, hooks, dependencies, build scripts or tests.
A separate evaluator processes candidate code without publication credentials.

Please resolve these questions with concrete failure cases and acceptance tests:

1. What exact permissions and repository topology are necessary? Evaluate a real
   fork against a standalone staging repository; do not assume any two repositories
   support cross-repository PRs. Separate staging write access, upstream PR creation
   and merge authority. Identify where GitHub scopes end and DAIA enforcement begins.
2. Bind publication to assignment ID, agent, repository identity, exact base SHA,
   resulting tree/patch digest, path scope, resource budget and expiration. Specify
   which fields the worker may suggest and which come only from trusted state.
   Cover renamed/deleted files, symlinks, submodules, file modes, binary patches,
   encodings and case/path normalization. An allowed path is not safe code.
3. Define recovery when branch creation, commit creation or PR creation succeeds
   but the response is lost. Retries must find the same candidate, not duplicate
   PRs or overwrite a different branch. Address crashes, concurrent submissions,
   stale bases, revoked assignments, token expiry and failed token revocation.
4. Design secret-free CI and evaluation. Include fork workflow settings, manual
   approvals, caches/artifacts, reusable workflows, dependency/install hooks and
   follow-up workflow triggers. Read-only GITHUB_TOKEN alone does not remove other
   secrets. Explain how approved evidence remains bound to the exact evaluated SHA.
5. Assume all reviewers approve a malicious patch. Prove the candidate cannot
   obtain secrets, change active publisher policy, merge itself or release/deploy.
   Also show a legitimate patch can be published and evaluated successfully.
6. Bound per-assignment and aggregate resource consumption. Many identities must
   not turn one contributor into unlimited PRs, CI minutes or independent votes.

Deliver: a minimal architecture, permission matrix, publication/recovery state
machine, adversarial plus useful-work acceptance plan, and go/no-go conditions.
Recommend one first implementation path. Call out uncertainty rather than adding
speculative governance machinery. Include an approximate engineering effort range
with assumptions, not an asserted delivery date.

Primary starting points, to recheck at review time:

- https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation
- https://docs.github.com/en/actions/concepts/security/compromised-runners
- DAIA `docs/worker-execution-boundary.md`, `docs/maintainer-delegation.md`,
  `src/daia/contributor.py`, and `.github/workflows/ci.yml` at the pinned commit.

## Human-carried research exchange

An agent may propose this brief to a willing user. The user chooses whether to
send it to a model or research service and brings the answer back. Preparing a
brief does not authorize automatic external messages or provider spending.

Use only public, intentionally exported context. Bind the request to its ID, exact
text/context digest and source revision. Store the returned answer as untrusted
research, with the request link, receipt date, artifact digest, citations and the
provider/model details reported by the user (unknown if unavailable). Preserve
attachments outside the executable checkout until inspected. Do not fabricate
cryptographic provider provenance for copied text.

A returned answer is not a new independent voter, proof of correctness, a consent
extension or execution approval. It may inform normal evidence review. Reserve
requests for a concrete uncertainty that affects a decision; ordinary development
continues without waiting unless that decision is genuinely required.

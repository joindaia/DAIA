# Personal subscriptions in isolated DAIA workers

Research received: 13 September 2026.

## Provenance and status

This is an English editorial record of the external research report supplied by
the project steward, not a verbatim transcript or a DAIA verification report.
Personal identifiers have been omitted. The supplied report used conversation-local
`filecite` and `cite` references rather than retrievable source URLs. Those references
cannot serve as public evidence and have not been reproduced as working citations.
Provider claims below remain **reported unless verified in the follow-up below**. In particular,
new authentication features, token lifetimes, subscription budgets and terms must be
checked against current official sources before implementation depends on them.

The [research brief](../research-briefs/personal-subscription-worker-auth.md) records
the question. Existing DAIA evidence is tracked separately in
[worker execution boundary](../worker-execution-boundary.md).
This document does not approve a deployment, change consent or authorize exposing
provider credentials to an untrusted worker.

## Two separate boundaries

Machine isolation prevents hostile task code from reaching host files, browser
profiles, SSH agents, control sockets, private networks and DAIA signing state.
Account isolation limits what authenticated provider requests can do. A token kept
outside the guest can still confer excessive authority if a proxy authenticates
arbitrary guest requests. Token secrecy alone does not establish inference-only use.

The supplied report describes DAIA's native Codex/KVM tests as using a synthetic
Responses provider. Those tests are not evidence of real subscription authentication,
provider refresh, account confinement or provider approval.

## Reported provider assessment

| Route | External report's assessment | Remaining evidence |
| --- | --- | --- |
| Claude Code with subscription setup-token | Feasible with explicit limitations: reportedly inference-only | Verify current official scope, lifetime, eligible plans and programmatic-use terms; demonstrate external credential binding with the unmodified client |
| Claude setup-token placed inside the guest | Functional experiment only | Hostile guest code can steal the credential and consume inference capacity outside the assignment |
| Native Codex ChatGPT login | Not demonstrated to satisfy strict account isolation | Guest-resident credentials are exposed; report says OAuth requests connector read/invoke scopes |
| Codex with Docker credential proxy | Token secrecy may be achievable; inference-only authority remains unproven | Test non-inference operations, including connectors, separately from token extraction |
| Dedicated provider account | Possible explicit concession | Reduces available personal data; does not prove inference-only authority or satisfy the original personal-account guarantee |

These are the report's conclusions, not confirmed compatibility claims.

## Authentication and lifecycle claims to verify

The report describes Codex browser and device login, with credentials stored in file,
keyring, automatic or ephemeral modes. A file with mode 0600, a keyring in the same
hostile security domain, or in-memory storage does not isolate secrets from arbitrary
guest execution. Copying a personal auth file into a worker is not an acceptable
production shortcut.

Docker Sandboxes reportedly keeps supported OAuth credentials host-side and substitutes
sentinels in the guest, including refresh-token handling. Verify the actual pinned
runtime and provider kit: supported login, storage ownership, interception destinations,
refresh, unbinding, restart and revocation are separate properties. Hostname-level
credential injection alone does not constrain HTTP methods, paths or account actions.

The report says Claude `setup-token` produces a one-year inference-only subscription
credential consumed through `CLAUDE_CODE_OAUTH_TOKEN`, and that Remote Control rejects
it. It also reports a separate subscription budget for programmatic Claude usage.
These particularly consequential claims require direct official-source verification.
Do not assume an exhaustive account capability matrix from one documented denial.

Normal native Claude login reportedly stores credentials under its configuration
folder. Moving that folder inside a disposable VM protects the host but does not
protect the credential from the guest. The proposed combination of an inference-only
setup-token, Docker proxy and unmodified Claude client remains an integration hypothesis.

Logout, deletion of a local file, removal of a proxy binding and provider-side token
revocation are different operations. Test each relevant lifecycle guarantee rather than
assuming logout revokes every previously issued token.

## Conditions of use

The report distinguishes a participant using their own original client to produce a
contribution from lending an account, pooling subscriptions or selling inference access.
Finite consent and assignment limits help describe the former but do not themselves
prove contractual permission. Paid development work and resale of provider services
also require separate analysis.

Verify current official terms for voluntary public contributions and paid third-party
assignments independently. The report recommends provider confirmation before a
commercial marketplace launch. This is a research recommendation, not authorization
to contact providers. No claim of provider approval is made.

## Proposed Linux/KVM experiment

Reuse the existing isolated worker and assignment-bound helper. Do not redesign the
scheduler or make a local model a prerequisite for answering the subscription question.

1. Verify official provider documentation and the pinned client's behavior first.
2. Prefer an externally held, genuinely inference-limited credential if supported.
3. Run one real public development task with the original client: investigate a failing
   test, produce a bounded patch, run tests, heartbeat and submit through the helper.
4. Re-evaluate the patch in a fresh environment without provider credentials.
5. Exercise hostile code directly; model refusal is not the security boundary.
6. Repeat with interruption, pending-result recovery, binding removal and fresh guests.

The external report proposes deliberately injecting a real Claude token into a first
functional guest to demonstrate its exposure. DAIA has **not adopted that step**.
A synthetic secret can demonstrate that exposure without risking a real long-lived
credential; real authentication should be attempted only with an explicitly scoped,
reviewed credential path and bounded consumption.

Keep three channels separate: assignment heartbeat/result submission, public research
and dependencies, and model inference. The model route must not become a general
subscription-to-API service or a destination-selectable authenticated proxy.

## Acceptance evidence

| Boundary | Required evidence |
| --- | --- |
| Host files | Direct paths and symlinks cannot reach synthetic host canaries; no personal mounts or inherited credentials |
| Host integrations | No SSH signing, Docker control socket, browser bridge or general host-side MCP |
| Network | External receivers confirm denial of host/private/metadata/IPv6 routes, redirects and private DNS resolutions; public research succeeds |
| Provider secrets | Guest filesystem, environment, process state and observable traffic contain no real credential |
| Provider authority | Non-inference account and connector requests fail outside guest-controlled configuration |
| Useful work | Real provider inference produces a patch independently tested in a fresh evaluator |
| Assignment | Only assigned operations; changed pending retries fail; exact retries produce the same receipt and one result |
| Lifecycle | Restart preserves only authorized assignment state; expiration/unbinding and watchdog cleanup terminate inference access |

A guest timeout is not independently sufficient evidence of network denial. A hidden
token is not sufficient evidence of account confinement. A short functional run does
not establish refresh behavior. No test result should be inferred from this proposal.

## Windows and release sequencing

Use Linux/KVM as the first reference. The supplied report flags Windows Docker
host-side MCP reachability as unresolved in the examined configuration; revalidate
that against current repository evidence and the pinned runtime before using accounts.
Windows must pass the same boundaries, not a weaker checklist. Disable SSH forwarding,
avoid implicit personal workspaces and distinguish stopping a VM from destroying its
state. Docker network policy alone is not evidence of post-resolution private-IP denial.

Next milestone: source-verified provider authentication design, followed by one real
subscription task with external credential and account confinement. Claude is the
report's suggested first candidate, conditional on verifying its inference-only claim.
Codex remains an explicit research track. Public admission and production cutover do
not follow automatically from either a successful model response or this report.


## Primary-source follow-up — 13 September 2026

Official [Claude authentication documentation](https://code.claude.com/docs/en/authentication#generate-a-long-lived-token)
confirms a one-year subscription setup-token for Pro, Max, Team and Enterprise. It
permits model requests but not Remote Control or retrieval of Claude.ai connectors.
Locally configured MCP remains usable. Bare mode does not read that OAuth variable.
This verifies the documented capability, not a DAIA integration or complete endpoint audit.

The [programmatic CLI guide](https://code.claude.com/docs/en/headless) supports
`claude -p`. It warns that ordinary print mode discovers project hooks and MCP
configuration without an interactive trust prompt. The subscription probe therefore
needs a clean guest HOME and curated initial task configuration. All later task code
remains untrusted. The inspected page did not establish the report's specific
June 15 subscription-credit change; that billing claim remains unverified.

Docker's [credential documentation](https://docs.docker.com/ai/sandboxes/configuration/credentials/)
confirms external credential injection and guest sentinels, with OAuth passthrough
explicitly reducing isolation. Its [Claude guide](https://docs.docker.com/ai/sandboxes/agents/claude-code/)
and [kit reference](https://docs.docker.com/ai/sandboxes/customize/kit-reference/)
are the starting points for a pinned integration. General OAuth proxy support is
not proof that the inference-only setup-token route works unchanged.

### Concrete preparation gate

Before asking a participant to authenticate:

1. Pin the original Claude binary and runtime; start without inherited credentials.
2. Use a synthetic sentinel and a synthetic upstream secret to test the selected
   runtime's credential injection. Do not implement a new general-purpose broker
   merely because the runtime integration has not yet been examined.
3. Confirm the upstream sees the synthetic secret while the guest sees only the
   sentinel. Reject other destinations; stop the binding and confirm subsequent
   requests fail. Check logs and returned errors do not expose the synthetic secret.
4. Repeat through the full guest networking path, not just a proxy unit test.
5. Only then request participant login for one bounded real development task and
   provider-side negative checks, without placing real credentials in the guest.

Current execution status: source verification completed; no Claude binary was found
on the current shell PATH. Existing native KVM harness files are present. No Claude
installation, login, real inference, token transfer or provider-account test occurred
in this follow-up. A login request would currently be premature: the external token
binding still needs credential-free integration evidence.

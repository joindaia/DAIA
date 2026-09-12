# Public launch and an autonomous DAIA environment

Design brief reviewed 11 September 2026. Proposed controls below are not implemented
or a claim of deployment readiness. See the [public-exposure threat model](daia-threat-model.md)
and the existing [delegated-orchestration brief](delegated-orchestration.md).

## Target and first release

DAIA should operate on its own infrastructure and project accounts. Agents should
research, code, test and eventually execute approved routine changes without access
to the operator's personal environment. Assume a malicious task can pass review:
review is a quality check, not the boundary protecting personal data.

Open participation is the target. Start the rollout with a small invitation cohort
to exercise the same bounded join flow, then remove manual admission after its checks
pass. Registration is not proof of independent ownership or permission to administer
DAIA. Keep the website deployable separately from the coordinator.

The immediate milestone remains a useful scheduled two-agent development round.
Hosting preparation can proceed while it runs; it does not establish that milestone.

## Current evidence and gaps

| Component | Implemented or tested | Still needed for the proposed launch |
|---|---|---|
| Static website | Four Astro routes; dated north star and milestones; no coordinator connection | Domain, reviewed publication and release artifact |
| Coordinator | Authenticated private-tailnet MCP; bounded payloads, leases, consent and signed receipts | Public authentication, ingress limits, service supervision, measured recovery and retention |
| Contributor helper | Local signing, persistent allowance, receipt recovery; Windows/Linux tests | Separate credential custody and tested containment of the parent agent and all tools |
| Joining and updating | Maintainer-assisted Python/helper setup | Versioned public installer, explicit update acceptance, compatibility and rollback tests |
| Execution | Contributed evidence is data; verifier does not execute uploads | Disposable evaluator and independently recorded results before running contributed code |
| Autonomy | Assigned production/review; shadow planning direction | Measured rounds and scoped execution grants; no automatic elevation or deployment today |

## Separate the operator, the service and each job

1. Deploy from a reviewed source artifact to a DAIA-only VPS. Do not copy a developer
   home, browser profile, personal agent history, SSH configuration or private runtime
   snapshot onto it. Use fresh DAIA service credentials and minimal operational data.
2. Give the VPS no membership of the operator's personal tailnet, route to home
   services, mounted personal storage, SSH-agent forwarding or personal connectors.
   Administration connects inward with a dedicated key. Recovery secrets and cloud
   billing/account control stay outside both the agent runtime and the VPS workload.
3. Keep the coordinator and credential-holding executor separate from disposable job
   execution. A container on the same kernel is a partial boundary; evaluate a separate
   worker VM or micro-VM for hostile executable workloads. If the chosen small VPS
   cannot support the required isolation, keep executable workers off that host.
4. Run the agent process and its tools inside the dedicated environment. Isolating
   only the shell while leaving personal filesystem, browser or MCP tools connected
   does not meet the requirement. Contributors need this protection on their machines
   too; moving only the coordinator to a VPS does not isolate their hosts.
5. Let a narrow executor apply grants to exact repositories, actions and artifact
   digests. Job text, agent votes and changes to repository instructions cannot expand
   those grants. Keep policy, credential custody and the executor's own update path
   outside ordinary job-write authority. No general root SSH or unrestricted sudo.

A compromised DAIA service can still damage DAIA data, availability or reputation.
Retention, spend caps, backups and revocation bound that remaining risk. This design
does not claim zero risk or prevent disclosure of personal data deliberately supplied
in a task. Initially accept public-source work only; private customer jobs need a
separate data-handling design.

## Keep useful tools

| Capability | Intended boundary | Acceptance example |
|---|---|---|
| Public web search and page reading | Broker without personal cookies or credentials; read methods; validate resolved IPs and every redirect; block private, loopback, link-local and metadata destinations; cap time and size | Find documentation on unfamiliar public sites; a redirect toward an internal endpoint is denied |
| Source editing | Fresh workspace with only approved inputs; no host home, sockets or other jobs mounted | Produce a real patch; attempts to read a synthetic secret outside the guest fail |
| Dependencies and tests | Broker fetches lockfile-pinned, hash-verified artifacts into a read-only cache; install hooks, builds and tests have no raw network, or use the same constrained broker; resource limits apply | Build a real dependency-using project; malicious install hooks have no host credentials or route to them |
| DAIA operations | Sidecar outside the guest mediates registration, status, work requests, heartbeat, release, signing and submission; validates each assignment and exact envelope; no raw token or signing-key access | Valid result gets a recoverable receipt; forged target or expired grant is rejected |
| Repository work | DAIA-only GitHub App operations; reviewed scope and short-lived tokens kept outside job tools | Submit a patch or PR; unrelated repository and account administration denied |

Search queries, logs and submissions are all possible output channels. Filtering
network destinations alone cannot protect a secret that the agent can read. Keep
secrets out of the context and workspace first. Public web content remains untrusted.
The worker uses bounded local tools to that sidecar; only the sidecar authenticates
to the coordinator. Bind the local channel to one worker identity and its grant.
Use supported provider authentication; do not extract or share subscription sessions.
Test each supported CLI/desktop configuration rather than assuming common isolation.

## DAIA identity and autonomy

Use a dedicated GitHub organization and a GitHub App as the operational identity.
Install it only on DAIA repositories, with the permissions needed for a particular
role. Keep the app's private key in the executor's credential store. A short-lived
installation token is still a credential; do not hand a broad one to arbitrary jobs.
GitHub supports apps acting as themselves with selected permissions and repository
access ([GitHub App documentation](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps)).

Create a project mailbox for DAIA communication. Use a separate recovery mailbox or
owner-controlled recovery route that agents cannot read, so ordinary mail access does
not become password-reset authority over GitHub, domain or hosting accounts. Treat
incoming mail as untrusted task input. Outbound sending needs an explicit policy and
limits before enabling it. No accounts, mailbox or repository transfer are created by
this brief; names, domain, recovery route and billing remain release inputs.

Grant autonomous routine actions in stages: proposals and patches, then execution
within a tested scope. Keep permission expansion, recovery and budget increases under
separate owner control at first. Normal work need not ask the owner each time after a
specific grant is established. This does not require paid branch protection, but CI
alone is not an authorization gate: enforce the action in the credential-holding
executor and test bypass attempts under the previously approved policy.

## Joining and approved updates

A future one-command bootstrap must identify an exact reviewed version and artifact,
verify its origin before credentials are supplied, and create the isolated environment.
Running an npm command under a personal account is not isolation. Do not advertise an
unpublished package name or encourage following an unreviewed latest release.

Show the proposed helper/tool/permission changes, accept one release explicitly, drain
or recover existing work, back up state, migrate and restart, then verify compatibility
and receipts. Roll back on failure. Preserve identity, deadlines, consumed allowance
and stop state; accepting an update is not renewed contribution consent. Report version
incompatibility clearly and stop new claims while keeping recovery available where
compatible. The current helper does not implement this updater.

## Delivery slices and release evidence

These are engineering estimates, not deadlines; they assume a supplied domain and
VPS access, supported provider authentication and no major findings during testing.

| Slice | Planning estimate from this baseline | Evidence before release |
|---|---|---|
| Static website | 1–2 working days | Reviewed copy, mobile/browser checks, only static build output published, working HTTPS/domain |
| Separate VPS invitation pilot | Roughly 1–2 weeks | Public auth and limits, no personal environment access, restore/restart tests, 48-hour bounded soak, participant host isolation checked |
| Open join flow | Roughly 2–4 weeks total, reassess after VPS slice | Fresh-machine installer and update/rollback tests; abuse/queue/storage caps; supported-client matrix; adversarial isolation and useful-work tests |

Dates do not override a failed gate. General autonomous deployment, paid work and
strongly isolated arbitrary execution may take longer and are separate grants.

Next implementation slice: public service boundary. Add a tested deployment profile
for TLS/authentication, strict routing and request limits while retaining current
private-tailnet behavior. In parallel, prototype one disposable worker and run one
real code task plus the hostile-input exercises from the threat model. Do not expose
the current development adapter by merely widening its bind or accepted origins.

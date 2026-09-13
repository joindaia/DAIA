# Worker execution boundary before public-cohort migration

Status: required deployment gate; full worker isolation is not yet established.

The closed HTTPS gateway authenticates clients and limits admission. It cannot
make job content safe when the coordinator is compromised. A data-only workload
label, a signed result, or a source checksum does not constrain an agent's tools.

## Required boundary

Run untrusted job processing without access to operator credentials, personal
files, other projects, host IPC, SSH agents, container-control sockets, or the
operator's network. Private file modes alone do not separate processes running
under the same operating-system user.

The worker must receive only a prepared project snapshot and explicit job inputs.
Do not mount an operator checkout wholesale: ignored files, Git configuration,
hooks, credentials, and private runtime state are outside the job. Use a clean
export of an approved commit. Clear inherited environment variables. Keep helper
signing credentials outside the execution environment and expose only bounded
contributor operations through a trusted broker.

Web research remains a supported requirement. Introduce it through an explicit
broker or network policy that blocks private networks and metadata services;
sharing the host network does not meet this gate. Build tools may operate inside
the project sandbox. Merge, deployment, and spending remain separate privileges.

Sandboxing one shell command does not sandbox the surrounding agent session.
Every file, browser, shell, MCP, and process tool available to the job-consuming
agent must respect the same boundary. Escalation into the operator environment
must not be available to that worker.

## Required acceptance evidence

- A job cannot read synthetic secrets placed outside its project, including
  through symlinks, inherited descriptors, environment, or host process access.
- A job cannot reach personal-network endpoints, metadata services, operator
  sockets, or privileged tools; explicitly permitted research still works.
- Attempts to request broader tool access are refused outside model judgment.
- Existing helper identity, pending receipts, finite consent, and usage survive
  separation and restart without exposing the signing key to job code.
- Test the actual worker session and its complete tool surface, not just a child
  shell. A malicious job test must fail to cross the boundary.

## Integrity work alongside isolation

Pin approved releases and verify signed artifact metadata against a separately
provisioned trust root, with version and expiry checks. Server startup checks are
useful but do not prove remote runtime integrity after root compromise.

Independently authorize immutable job manifests containing the project commit,
input digests, objective, allowed capabilities, limits, recipient scope and expiry.
The helper must validate authorization before delivering job content to the model.
A coordinator-held signing key alone does not protect against that coordinator's
compromise. Cryptographic authorization establishes provenance and scope, not
whether the content is harmless.

## Evidence so far

A disposable Linux bubblewrap process successfully ran with a separate network
namespace, an empty temporary filesystem, and no home or Windows mounts. This
establishes availability of one isolation mechanism only. It does not establish
isolation of the existing desktop worker or a usable web-research broker.

Keep public admission empty until the intended workers meet the boundary above
and the separate migration/reconciliation checks pass.

## First Linux execution primitive

`python -m daia.isolation --input APPROVED_SNAPSHOT --timeout 300 -- COMMAND`
starts a command with bubblewrap. The operator supplies a clean, immutable snapshot;
this is not an interface for arbitrary coordinator-provided mount paths. Input is
read-only at `/input`, scratch space is ephemeral at `/work`, the environment is
cleared, and network, home, host IPC and operator sockets are not shared. Symlinks,
special files and common private checkout directories in the snapshot are refused.
The host operating-system tools under `/usr` are available read-only. Missing
isolation support fails; there is no unconfined fallback.

The wall-clock limit is enforced outside the task. This primitive has real Linux
integration checks for hidden host canaries, read-only input, missing inherited
environment secrets, unreachable external network and deadline termination:

```sh
DAIA_RUN_ISOLATION_TESTS=1 PYTHONPATH=src python -m pytest tests/test_isolation.py -q
```

It is not yet connected to the desktop worker. It does not supply a model API or
research broker, persistent result export, or a per-task memory/process cgroup.
Combined stdout and stderr are buffered up to one MiB. Exceeding that limit
terminates the namespace with exit 125 and discards the captured output. Output is
forwarded only after the task exits, so a slow caller cannot suspend the task
deadline check. This is an output bound, not a memory or process-count limit for
the job itself. Standard output is untrusted task output. Input screening is not a secret detector.
Do not use this primitive alone as evidence that the full worker gate has passed.

## Existing desktop worker: negative boundary check

A diagnostic run of the existing worker, using its ordinary tools without requested
escalation, reported successful access to a synthetic canary inside the operator's
private credential directory. The result was written during that diagnostic run;
no credential contents were requested or recorded. This establishes a failed
boundary for that worker configuration, not a successful isolation test.

Its native hourly work schedule has been paused. Identity, consumed budget and
consent expiry were not changed. Do not resume scheduled job consumption or migrate
this worker into the public cohort until its entire tool surface has an enforced
separate execution boundary and the canary test fails as intended. Reconnecting MCP
or moving its project folder does not by itself provide that separation.

## Reproducible native Codex command probe

An opt-in test now exercises a named native Codex permission profile with root
access denied, minimal operating-system reads, the resolved Codex executable
readable, and the disposable task directory writable. Network access is disabled.
It uses an empty temporary Codex configuration home and makes no model requests.

```sh
DAIA_RUN_CODEX_SANDBOX_TESTS=1 PYTHONPATH=src python -m pytest tests/test_codex_permissions.py -q
```

On the tested Linux installation (Codex 0.153.4), this refused both direct and
symlink reads of an outside synthetic canary and a connection to a live host
loopback listener. An unsandboxed control first connected successfully to that
listener; the task still wrote its result inside its workspace. The test fails
rather than skips when explicitly requested and the executable or sandbox fails.

This is evidence for the native command profile only. It does not configure the
existing desktop task, constrain its other tools, provide a research broker, or
establish isolation of the model process and inherited session state. Keep the
worker schedule paused and admission empty until the complete session meets the
acceptance requirements above. Do not use this probe as a worker launcher.

## Assignment-only trusted helper interface

The helper can serve a restricted stdio MCP interface for an already assigned job:

```sh
python -m daia.contributor --invite /private/invite.json \
  --job-authority /private/approval.json --assignment ASSIGNMENT_ID
```

The operator must supply the exact existing assignment ID and an independently
approved policy. This mode requires saved registered identity; it never creates a
replacement identity or claims work. Its only tools are `heartbeat` and
`submit_result`, whose inputs cannot select another assignment. The helper checks
the pinned assignment under its operation lock, both before and after recovery.
A completed or changed assignment requires a new operator-controlled session.
New heartbeat and submission operations also require the corresponding
`heartbeat` or `submit_result` capability in the signed authorization. A previously
signed pending submission may still be retried exactly after consent/authorization
expiry, using the existing receipt-recovery rules; this permits no new signature
or additional work.

This is the trusted side of a future worker channel. Keep its process, invite,
state, approval configuration and stdio launcher outside the untrusted worker.
The isolated worker should receive only the prepared input and a connection to
this interface, not permission to launch or reconfigure the helper. Connecting it
to an ordinary desktop task does not isolate that task's other tools. The channel
transport, whole-session isolation and permitted research access remain unfinished;
this mode alone does not authorize resuming workers or public admission.

Tests cover scope substitution before and during recovery, refused extra tools,
missing operation capabilities, invalid CLI scope, preserved identity/budget/deadline,
and exact pending replay after expiry. A real stdio-to-HTTP exercise uses synthetic
credentials and independently signed job authorization to submit one result through
the restricted interface. It explicitly loads the current source in its child
process instead of relying on an unrelated editable installation.

## Explicit socket transport primitive

The Linux execution primitive accepts an optional trusted-launcher argument:
`--assignment-socket /private/helper/assignment.sock`. It exposes only that socket
at `/run/daia-assignment.sock`, without mounting its containing directory or sharing
the host network namespace. The source must be a canonical Unix socket owned by
the launcher user, inaccessible to group/others, in a private directory owned by
that user. The trusted launcher must keep the socket and its parent under exclusive
control throughout execution.

Socket metadata does not identify the service behind it. Only a dedicated
assignment-helper endpoint may be supplied; never an SSH agent, container-control
socket, generic proxy or other host service. The argument is not a worker-selectable
MCP operation. A read-only socket mount permits protocol communication; it does not
make the remote service's operations read-only.

A real namespace test exchanged bounded synthetic messages through this one socket
while an adjacent synthetic signing secret remained unavailable and workspace
writing still worked. Existing network/environment isolation tests also passed.
This establishes a transport primitive, not the complete helper relay: bounded MCP
framing, backpressure, disconnect cleanup, the real restricted MCP exchange and the
full job-consuming agent session still require integration and verification.

The subsequent real MCP integration test (`tests/test_isolated_mcp.py`, opted in
with `DAIA_RUN_ISOLATION_TESTS=1`) connected a process inside the namespace to the
restricted helper outside it. The client initialized MCP, listed exactly two tools,
was refused new work, heartbeated and submitted a synthetic signed assignment.
The helper invite and saved signing state were inaccessible inside the namespace;
identity, consumed budget and consent deadline were unchanged after submission.
The test relay is for known small fixture messages only. It is not the production
bounded relay, nor a full Codex/Claude session or research-access acceptance test.

## Full-worker microVM implementation target

The next full-worker prototype targets one disposable, mountless Docker Sandboxes
microVM per public-source assignment. The native agent, subprocesses, MCP servers,
package installation and browser must all remain inside that guest. The existing
assignment helper belongs outside it. Existing bubblewrap tests prove individual
component boundaries, not this full-worker architecture.

The initial route exports only a bounded result and source patch for a fresh
credential-free evaluator. The worker receives no host mounts, personal profile,
SSH forwarding, host-side MCP servers or GitHub credential. A separate controller
owns assignment binding, signing, consent and lease maintenance. Security updates
remain a separately authorized operation over exact artifact bytes.

Documentation verified on 2026-09-12:

- [Installation prerequisites](https://docs.docker.com/ai/sandboxes/install/):
  Linux requires KVM; Windows requires Windows 11 and Windows Hypervisor Platform.
  A running hypervisor alone does not establish that all prerequisites are met.
- [Mountless creation](https://docs.docker.com/reference/cli/sbx/create/): omit
  the workspace path. Stop/restart is not job cleanup: guest state persists until
  removal, as described in the [architecture](https://docs.docker.com/ai/sandboxes/architecture/).
- [Network deny rules](https://docs.docker.com/reference/cli/sbx/policy/deny/network/):
  an allowed hostname is not checked against CIDR rules for its resolved address.
  Therefore a domain allowlist plus private-IP denies is insufficient evidence.
- [Upstream proxy configuration](https://docs.docker.com/ai/sandboxes/configuration/upstream-proxy/)
  is experimental and includes direct and bypass routes. Explicit proxy settings
  alone do not establish externally enforced, fail-closed egress.

The current development preflight found no sbx command on either inspected PATH,
no KVM device in the WSL environment, and a Windows hypervisor reported present.
No runtime was installed or provider login performed. A subsequent direct Windows Hypervisor Platform API probe succeeded with
`HResult=0`, `HypervisorPresent=true`, and `WrittenBytes=4`. Repeat it with
`scripts/probe_windows_hypervisor.ps1` in Windows PowerShell. The earlier DISM
feature query required administrator access; the read-only API probe did not.
[Microsoft documents this capability](https://learn.microsoft.com/en-us/virtualization/api/hypervisor-platform/funcs/whvgetcapability)
as a platform availability check. It does not prove a sandbox starts or its
network/account boundaries work. Do not fall back to host task execution.
The supplied research test package has not yet arrived or been independently run.

Release evidence must include both a genuinely useful native-agent patch and an
executed hostile workload unable to reach host secrets, private networks or
unwanted cloud-account operations, even with positive reviews. Provider login and
refresh behind an inference-only policy, actual external egress enforcement,
watchdog cleanup, and independent updater authorization remain unproven.

### Windows runtime installation evidence

The per-user Docker Sandboxes v0.42.1 MSI was installed successfully (installer
exit 0). Its SHA-256 matched the official release asset digest:
`7889fb867090ab81ebbcc950d734e76976c2e7b52ab4ca359cb205b0c51e25d3`.
Windows Authenticode reported a valid Docker Inc signature before installation.
A direct process invocation with shell execution disabled returned
`sbx version: v0.42.1 cc6e400a4a3ce3ce5e0b2b77b8ee352aac854c64`, exit 0.
The shell invocation from WSL did not reliably execute the binary; use an explicit
native process launcher and check the child exit status for subsequent probes.

This supersedes the earlier missing-runtime preflight. No Docker/provider login,
worker creation, credential import or actual assignment execution has been done.
Installation and a working CLI are prerequisites, not isolation acceptance.

### Native daemon preflight and account gate

The daemon initially failed through the inherited WSL process environment. A
long-form, dedicated TEMP/TMP directory avoided the short-path directory error.
The next failure was traced to containerd's EROFS plugin: `mkfs.erofs` could not
be found. Supplying a native PATH containing the installed `bin`, `libexec`, and
Windows system directories, with `PATHEXT=.COM;.EXE;.BAT;.CMD`, allowed daemon
startup. These overrides were confined to the launched process, not global OS
settings. No existing sandbox state was deleted.

Verified runtime changes:

- `settings set ssh.agentForwardingEnabled false` succeeded; daemon restart and
  subsequent `settings get` confirmed `false`.
- The fresh global network policy was initialized with `policy init deny-all`.
- `create shell --name daia-boundary-probe --cpus 2 --memory 2g --deny-network **`
  then refused with HTTP 401 because no Docker account session exists. No task
  workspace or model credential was supplied. A created/booted VM is not proven.

The next external prerequisite is a Docker account login through its supported
native flow. Do not borrow an unrelated personal account, collect session tokens,
or treat the failed create as a completed isolation test. After login, repeat the
mountless shell preflight before adding provider authentication or task data.

The independent review of the restricted MCP fixture found no actionable issue;
its scope remains the synthetic namespace exchange, not the complete microVM.

### Repeatable Windows operator invocation

From the repository in Windows PowerShell, launch a child PowerShell process:

```powershell
powershell.exe -NoProfile -File ./scripts/windows-sbx.ps1 version
powershell.exe -NoProfile -File ./scripts/windows-sbx.ps1 settings get ssh.agentForwardingEnabled
```

The launcher supplies the known-working native PATH/PATHEXT and dedicated
long-form temporary directory, and propagates the CLI exit code. It changes no
persistent OS environment variables. It is an operator convenience, not a worker
security boundary; never expose it to a task. A running daemon retains its launch
environment until restarted.

Once a DAIA Docker account is available, the same launcher can invoke `login`
through Docker's native flow. That remains an account action, not permission to
import unrelated credentials or begin real assignments.

The saved script was executed through native Windows PowerShell: version returned
v0.42.1 with exit 0, SSH forwarding returned false with exit 0, and a deliberately
invalid CLI command returned exit 1. No VM was created during these checks.


### Booted microVM and gateway findings (2026-09-12)

The earlier account gate is resolved. A DAIA-owned Docker account successfully
logged in through the native password-stdin route. No model-provider credentials
were imported. A mountless shell guest booted on sbx v0.42.1 with its own kernel
7.0.12, two CPUs and 2 GiB memory. Its template digest was
`sha256:5fc81bc7a127e59d81b244a06831ae3212a0310b2e5a0349c54e29249e45e919`.
No workspace or published ports were configured, and SSH forwarding remained off.

The default MCP gateway was nevertheless reachable from the guest with network
`deny **` active: initialization returned HTTP 200 and `tools/list` exposed
`code-mode`, `mcp-add`, `mcp-config-set`, `mcp-exec` and `mcp-find`. Adding an
explicit deny for `mcp-gateway.docker.internal` did not prevent initialization
after guest restart. `policy ls --wide` confirmed both deny rules were stored.
A separate mountless guest created with `--static-mcp ""` exposed the same tool
set. An empty static set is therefore not a gateway-disable mechanism in this
version. Both test guests were stopped afterward; stopping preserves their state.

These probes invoked no gateway tools and demonstrate neither host-code execution
nor credential theft. Listings alone do not prove invocation permission. However,
network denial and empty static configuration do not establish the required
absence of a host gateway. Docker documents MCP authorization as a separate
[organization Cedar policy layer](https://docs.docker.com/ai/sandboxes/governance/access-controls/mcp/),
without a local network-style preset. The installed CLI exposes only network deny
and check subcommands; no organization profiles were available in this account.
Do not resume workers on the strength of a successful VM boot. Enforced MCP
capability restrictions, external egress enforcement and provider-account scoping
remain release gates.

### Received reference kit: isolated contract run

The supplied research kit's 24 contract tests and one positive-fixture test passed
inside the existing Linux bubblewrap primitive. The fixture checks that the
original version-comparison implementation fails and that a supplied reference
patch passes six regressions. Only copied source files and the installed packaging
26.3 package were supplied as read-only input; scratch storage was ephemeral and
no network, operator home or credentials were mounted. This differs from the
kit's pinned packaging 25.0 environment, so it is not an exact dependency replay.

These are tests of the kit's reference contract, not production DAIA signing,
provider authentication, the Windows microVM, or a real agent-generated patch.
The external VM runner has not been executed. Its stdin write occurs before its
process-wait timeout; that runner needs bounded input delivery before it can serve
as the trusted controller for a guest that refuses input. Continue to require the
full negative-boundary and useful-native-agent acceptance tests above.


### Fixed nonempty MCP set: management-tool denial

A subsequent guest used an explicit fixed set containing one operator-prepared
remote loopback fixture with an empty `tools/list`. Unlike the empty flag, this
removed `mcp-add`, `mcp-config-set` and `mcp-find` from the gateway session.
Only `code-mode` and `mcp-exec` remained. Direct calls to all three missing tools
returned JSON-RPC unknown-tool errors. Calls through `mcp-exec` returned explicit
not-found errors, and requesting `mcp-add` through `code-mode` also failed.

`scripts/probe_static_mcp.py` repeats the exact listing and ten denial checks
inside that prepared guest. It supplies no server configuration or executable
JavaScript. The saved probe passed on sbx v0.42.1. It fails on an unexpected gateway
URL or response, and uses explicit checks that remain enabled with Python `-O`.
The outer trusted launcher still needs to bound the total process lifetime.

This is evidence for session-level management-tool exclusion only. The fixture
was a remote no-tool service, not a registered host command. The surviving
`code-mode` execution environment, session credential binding, another-session
access, and external network enforcement are not established by these checks.
A fixed set is a candidate integration route, not approval for real worker jobs.


Review correction: the four code-mode responses contained refusal text but no
`isError: true` flag. They therefore did not establish protocol-level failure.
The original ten-check success was too broad. The probe now requires an explicit
error flag and exact error content, rejects paginated listings, correlates both
JSON and SSE replies, and uses distinct request IDs. On the observed v0.42.1
responses, it must fail at the first code-mode check rather than report ten
verified denials. Six direct/indirect management-tool errors were observed.

No executable JavaScript was supplied. Client responses do not establish whether
an executor was created internally. The behavior of sessions with real tools
remains unverified.


The hardened probe was run against the live guest and exited 1 with
`Code-mode exclusion not established`, as expected from the missing error flags.
Seven JSON/SSE response-fixture regression tests pass, including wrong IDs,
pagination, missing error flags and explicit false error flags. These tests verify
the probe's refusal to overclaim; they are not gateway integration acceptance.

A separate network probe first reached an empty synthetic service from Windows.
The guest's HTTP request via `host.docker.internal` then returned an explicit
403 local-policy block. The alternate gateway hostname disconnected, and a raw
TCP connection to the host alias connected but returned no bytes. Those latter
outcomes are inconclusive; they do not establish a general TCP or private-network
boundary. The service and guest were stopped after the probe.


A receiver-observed follow-up used a new loopback canary with accept/request
counters. Windows controls before and after the guest attempts both read the
expected canary bytes. The receiver recorded exactly those two connections and
control requests, with no connection for guest HTTP, direct-socket HTTP or raw
non-HTTP bytes sent through the Docker host alias. HTTP returned a policy 403;
the direct socket attempts received zero bytes. This establishes non-arrival at
that tested service during the experiment, not a general IPv6, private-address,
DNS-rebinding or permitted-internet boundary.

The probe's response regression suite now has twelve passing cases. It also
requires initialization to return a session and negotiated protocol, rejects an
unexpected session replacement, permits empty bodies only for notifications, and
matches indirect error content exactly. The live strict probe still stops at the
code-mode error-flag check. These improvements strengthen evidence handling; they
do not turn that integration failure into acceptance.


### Windows proxy transport observation

A subsequent bounded probe in the existing mountless static test VM attempted
ordinary DNS resolution of the MCP hostname and received no address. The same
MCP initialization succeeded with HTTP 200 and a session header through the
configured HTTP proxy at `gateway.docker.internal:3128`. A direct guest TCP
connection to that proxy, carrying an absolute-URI HTTP request, also received
HTTP 200. No MCP tools or task code were executed.

During the short held connection, six Windows TCP-table samples of the runtime
and its direct children showed a loopback connection whose two ends belonged to
`sbx.exe`, plus unrelated-looking HTTPS sockets. No ordinary host TCP socket on
port 3128 appeared in that sampled process set. Three runtime listeners were
bound to IPv4 loopback; a direct unauthenticated GET to one returned HTTP 401.
The initial observer classified wrapped HTTP exceptions as transport errors;
the subsequent focused check established that 401 response explicitly.

This is a transport observation, not proof that the loopback pair carries the
MCP request, that every relevant process was covered, or that Windows Filtering
Platform cannot filter the path. Port numbers and process IDs are ephemeral.
A guessed firewall rule against guest port 3128 is not justified by these results.
The next enforcement experiment needs correlation of the actual gateway route,
a temporary rule scoped to that route, and simultaneous successful public-work
controls before and after restart. At that point the Windows process token was not
elevated, so no firewall change was attempted in that observation. The test VM was stopped afterward.


### Elevated Windows firewall experiment

After elevation was confirmed, a short test used an outbound TCP block rule
scoped to the installed `sbx.exe` and IPv4 loopback (`127.0.0.0/8`). All Windows
firewall profiles were enabled. The rule was observed in ActiveStore as enabled,
blocking and outbound. MCP initialization returned HTTP 200 with a session header
before the rule, while it was active, and after its removal. The test used the
existing static mountless VM and executed no MCP tools or real assignments.

Windows rejected the attempted IPv6 loopback selector (`::1`) with error
0x80070057 before that variant could be exercised. Cleanup ran after each attempt;
the named temporary rule was removed and the test VM was stopped.

The tested ordinary firewall rule does not close this MCP route. ActiveStore
presence is not proof that the gateway packets matched the rule; there was no
WFP packet trace or positive blocked-traffic control. This does not establish
that all external WFP enforcement is impossible, identify the gateway's actual
transport, or validate useful public egress. No broader firewall change or worker
admission follows from this result.


### Supported policy and alternative-runtime prerequisites

The [Docker MCP access-policy documentation](https://docs.docker.com/ai/sandboxes/governance/access-controls/mcp/)
explicitly describes organization-scoped Cedar enforcement and states that MCP
has no local preset. The installed CLI's `policy deny --help` exposes network
rules only. This supports the current local-policy limitation; it is not evidence
that every possible external gateway filter has been ruled out.

QEMU was absent from Windows PATH and the two inspected conventional installation
locations. An elevated DISM query reported `HypervisorPlatform` disabled, despite
the earlier successful hypervisor-capability API check. The feature was enabled
with `-NoRestart`; Windows returned `RestartNeeded=true` and state `Enabled`.
No reboot was initiated. Repeating the existing API probe still returned
`HResult=0`, `HypervisorPresent=true`, and four bytes written. Capability presence,
feature servicing state and a successful accelerated guest boot are distinct
checks; no QEMU boot has been demonstrated.

The [official QEMU download page](https://www.qemu.org/download/)
links Windows builds and the MSYS2 packaging route. Its
[security documentation](https://www.qemu.org/docs/master/system/security.html)
requires a virtualization accelerator and a supported machine type for its
virtualization security model; TCG is not a security-equivalent fallback. A
replacement trial must preserve the existing worker requirements, including
external egress enforcement, credential separation and useful native-agent work.
It does not relax the cohort cutover gate or approve a provider expenditure.


### QEMU/WHPX prerequisite trial after restart

The Windows installer listed in the Microsoft community winget manifest for
`SoftwareFreedomConservancy.QEMU` 11.1.0 was downloaded from the Windows build
provider linked by QEMU. Its SHA-256 matched
`f98a8aeb5f7faea9765b6dee28316c266cd179d80354a2fed8e50176f9a2e59f`
before and after copying to the native installer directory. Installation through
normal Windows elevation returned exit 0. Explicit process capture confirmed
QEMU 11.1.0 and the `whpx` accelerator. This records a test-runtime pin, not a
claim that it is the latest upstream release or approved for hostile workloads.

`scripts/probe_windows_qemu.ps1` initialized a Q35 machine with WHPX, no default
devices, no network, no disks or host mounts, and no guest execution (`-S`). QMP
capability negotiation, an ID-bound status response (`prelaunch`, not running),
and a host-requested shutdown all succeeded; QEMU exited 0. No TCG fallback was
configured. Warnings about an unavailable SVM CPU feature and interrupt vector 0
remain visible; the probe does not suppress or resolve them.

The first pipelined stdio attempts produced protocol errors or timed out and
were terminated. The successful probe keeps stdin open and waits for each QMP
response before sending the next command. This establishes the corrected
probe's behavior, not a diagnosis of every cause of the earlier errors.

This proves accelerator initialization and a bounded management lifecycle only.
A guest OS boot, hostile workload containment, external egress filtering,
credential separation, resource limits for a full job and useful native-agent
work remain required before worker admission or cohort cutover.


### Networkless Ubuntu guest boot under WHPX

An Ubuntu Noble cloud image (625,256,960 bytes, SHA-256
`612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354`)
was checked against its checksum list after `gpgv` verified that list using the
installed Ubuntu cloud-image keyring. The image and a locally generated NoCloud
seed were copied to a dedicated native cache and rechecked before launch.

QEMU booted a fresh QCOW2 overlay with WHPX, two vCPUs and 2 GiB configured guest
RAM, without a network device, host-directory sharing, or provider credentials.
A fixed trusted diagnostic reported kernel `6.8.0-139-generic`, only loopback,
no 9p/virtiofs/CIFS mount and no `/mnt/c`. Its result matched the run nonce. The
guest powered off, QEMU exited 0 before the 180-second timeout, and the disposable
overlay was removed. The verified base image remains cached for subsequent tests.
The guest's network-online wait delayed this intentionally offline first boot.

Serial output was treated as data. PowerShell initially serialized file-provider
metadata along with a matched log line; the private report was reduced to the
explicit diagnostic fields, and the runner now parses the marker JSON before
serialization. Raw logs and host paths are not publication artifacts.

This was a trusted prerequisite run under the current operator process identity,
not the separately restricted production runtime identity. It establishes an
actual guest boot and self-shutdown, not protection from hostile guest code,
hard host resource limits or safe public egress. Those remaining boundaries and
a useful native-agent task must still pass before admitting contributor work.


### Separate Windows runtime identity

A dedicated local `daia-runtime` account was created without administrator
membership. Its generated credential is DPAPI-protected in an operator-only
ACL-protected directory outside Git. The account has modify access to its own
runtime directory; it was not granted access to operator credentials. This OS
account does not create or renew any DAIA contributor consent.

A process launched with that account, without loading the operator profile and
with a cleared, explicitly rebuilt environment, passed three checks: its token
was not an administrator, writing its own test file succeeded, and reading a
synthetic file in the protected operator directory raised access denied. The
operator independently confirmed that file was unchanged, then removed it.
Under the same account, the diskless/networkless WHPX prerequisite probe reached
`prelaunch`, completed QMP shutdown and exited 0. A long encoded command failed
to launch with alternate credentials; using a short temporary script path worked.

This confirms one account/ACL boundary and WHPX availability without elevation.
It does not make every host file private, deny all network routes, protect other
jobs, or prove an untrusted guest cannot escape QEMU. A full guest boot under
this identity, protected immutable templates, resource limits and external egress
policy remain separate gates. No real contributor was admitted.

### Full guest boot under the restricted runtime account

The signed Ubuntu base image and fixed diagnostic seed were staged in a separate
Windows template directory. Its ACL grants the runtime account read/execute only,
with operator/system/administrator write control. Before launch, the operator
checked both file hashes. The runtime process confirmed a write-open of the base
image was denied and its token was not an administrator.

Under that identity, QEMU/WHPX booted a fresh writable overlay without a network
device or shared host filesystem. The nonce-bound diagnostic reported only
loopback, no Windows mount, and all guest checks passed. The guest powered off;
QEMU exited 0 without timing out. The runner removed the overlay in its cleanup
path, and the operator confirmed its protected synthetic canary was unchanged.

This extends the prerequisite from paused QEMU to an actual Linux boot under the
restricted account. It remains a trusted offline diagnostic, not a hostile-guest
escape test or a useful native-agent task. Per-job host isolation, external
network enforcement, provider-account restrictions and independent resource
limits are still required. The temporary launcher is a lab fixture, not an
immutable production controller. No contributor consent or admission changed.

### Repeating the offline guest prerequisite

`scripts/probe_windows_guest.ps1` accepts operator-selected `Base`, `Seed`,
`BaseHash`, `SeedHash`, `Nonce` and `WorkDirectory` parameters. Run it under the
restricted Windows runtime account, with a cleared environment, a signed-image
verification performed separately, and read-only templates. It does not create
accounts, change ACLs, fetch images, authenticate providers or admit work.

The seed must be a reviewed NoCloud diagnostic that emits exactly one serial line
prefixed `DAIA_BOOT_RESULT `, containing `nonce`, `checks_passed: true`,
`shared_filesystem: false`, `windows_mount_present: false` and `interfaces: ["lo"]`,
then powers off. Supply its exact hash and nonce independently to the runner.
These guest assertions establish trusted diagnostic behavior, not a security
attestation from a hostile guest. Never use an arbitrary contributed seed here.

The script refuses elevation, checks template hashes and denied write access,
boots only WHPX with no NIC or shares, limits the guest wait to 180 seconds, and
checks overlay deletion before emitting success. Private serial logs remain for
inspection. They are not public artifacts. This lab runner does not bound hostile
serial output, implement a crash-proof watchdog or replace production isolation.

The repository script completed a live run under the restricted account: exit 0,
matching guest diagnostic, both template write checks denied, no timeout and
`OverlayRemoved: true`. An independent host-side directory check found no guest
overlays remaining. A second invocation supplied an incorrect base hash and
failed with `Template checksum mismatch`, before overlay creation or guest launch.
These are local Windows results, not CI or full worker-release approval.

### Restricted networking: paired local canary experiment

QEMU's [user-network documentation](https://www.qemu.org/docs/master/system/qemu-manpage.html)
defines `restrict=on` as denying host/outside routing while preserving explicit
forwarding rules. A paired trusted-guest experiment exercised this on the installed
Windows QEMU/WHPX runtime under the non-administrator account.

The host bound a synthetic loopback TCP listener and first confirmed a local
connection succeeded. The guest used a fixed private test address and attempted
only that listener through QEMU's host alias, plus an explicitly configured
`guestfwd` channel to a private diagnostic file. With restriction on, the direct
connection was refused and the host saw no queued connection; the explicit
channel delivered the expected nonce. With restriction off, the same diagnostic
reached the listener and the host observed the connection. Both guests shut down
with exit 0; no overlays remained after cleanup.

The control run used reviewed diagnostic code only, no other destinations, no
provider credentials and no contributed work. It was not a worker configuration
change. IPv6 was disabled for both tests. QEMU emitted a WSAEventSelect warning
for the file-backed channel; successful nonce delivery is not proof of a usable
HTTP proxy or bidirectional channel. A real gateway, DNS/redirect and private/VPN
route checks, fail-closed gateway loss, provider restrictions and process-level
containment remain unverified. This test establishes only the paired IPv4 host
route and explicit diagnostic channel.

Static review also found a timeout cleanup race: image creation was killed without
waiting for process exit before overlay deletion. The runner now waits after
killing that process. This does not alter the successful-boot evidence above.
The corrected timeout branch was exercised against an actual Windows child
process holding a synthetic file with exclusive sharing. Deletion was first
confirmed blocked; the extracted timeout branch stopped and awaited the child,
after which deletion succeeded. This fault fixture did not use a real hung
`qemu-img`, and does not establish recovery after controller termination.

### Bidirectional HTTP and gateway-loss prerequisite

A subsequent restricted-guest run replaced the file sink with a TCP-backed
`guestfwd` to a synthetic host-loopback HTTP server. The server independently
matched the expected request path and returned the run nonce in a bounded HTTP
200 response. The guest validated the response body. The server then closed its
connection and listener. A second guest HTTP request received no response before
its timeout; a direct attempt to a separate, prechecked live host canary was
refused, and the host observed no queued canary connection.

QEMU and the guest exited normally; the operator found no remaining guest overlay.
The WSAEventSelect warning also occurred with the TCP-backed channel, so it was
not specific to the earlier file sink. It did not prevent the observed exchange,
but its cause remains unestablished. The timeout alone is not proof of general
network blocking; the independent canary observation supports only that tested
route. No public request, DNS policy, IPv6 route or provider login was exercised.

This demonstrates one HTTP exchange and loss of that gateway route. It does not
prove reconnect, concurrent clients, TLS tunnelling, or sustained native-client
operation. QEMU documents the direct chardev as a connection lasting for the
VM lifetime; its suitability for multiple independent proxy connections needs
explicit testing before choosing it as the production transport.

### Repeated HTTP connections: direct chardev transport is insufficient

A three-request experiment kept the synthetic host server listening and used a
new guest HTTP connection for each distinct, nonce-bound path. With the direct
TCP chardev configuration, the first exchange passed but the next two timed out.
The host observed exactly one request. This is an observed transport limitation,
not a successful general proxy test: the server was not intentionally stopped.
The direct-chardev configuration must not be used for native worker traffic on
the strength of the single-request proof. A fixed per-connection forwarder is
being evaluated separately, without expanding the guest's destination access.

The fixed per-connection command trial did not establish a replacement: all three
requests disconnected and the host received none. QEMU/libslirp logged GLib's
`Failed to execute helper program (No such file or directory)` plus a warning
that child setup callbacks are ignored on Windows. The intended PowerShell
executable and read-only bridge script both exist. The installed QEMU tree contains
GLib/libslirp DLLs but no filename containing `spawn`; missing GLib spawn-helper
packaging is a lead, not a confirmed root cause. No host networking rights were
expanded to compensate. The diagnostic guests exited and overlays were removed.
The fixed forwarder remains a private lab fixture, not a released worker feature.

### Windows command forwarding remains unsuitable after helper repair

Inspection identified GLib 2.88.3 strings in the installed DLL and references to
two absent spawn helpers. The exact MSYS2 `mingw-w64-x86_64-glib2-2.88.3-1` package
was fetched with its detached signature and verified against the official MSYS2
keyring at a recorded commit; the signer was absent from its published revocation
lists. Only the two helpers were extracted. Their imports require Windows system
DLLs and GLib; no replacement DLL was installed. The private evidence records
package/helper hashes and the keyring commit.

The helpers were added to an ACL-protected test directory and exposed only via
the runtime process PATH. The same three-connection test then progressed past
helper lookup, but failed with `Failed to dup() in child process (Bad file descriptor)`
for every connection. The guest observed three disconnects and the host received
zero requests. Thus resolving lookup does not make Windows `guestfwd ... -cmd:`
a working transport. The exact socket/descriptor incompatibility is not diagnosed.
Do not distribute the helper addition as a worker fix or relax network policy.

Both direct-chardev and command-forwarding routes are now rejected for native
worker release on this tested runtime. Further work should use a separately
validated transport, rather than repeating single-request tests. The installed
QEMU directory and system PATH remain unchanged; all trial overlays were removed.

### Linux KVM prerequisite after host restart

A later live check found `/dev/kvm` in WSL. The ordinary maintainer process was
refused access, but an explicitly authorized root prerequisite via the Windows
WSL launcher returned KVM API version 12 and successfully created and closed an
empty VM. No guest code executed and no device permissions were changed. This
supersedes the earlier device-absence observation only: an actual Linux QEMU boot,
a separate unprivileged runtime identity and network enforcement still need tests.
It provides a concrete alternative to further Windows libslirp command-forwarding
work; it does not make the personal WSL environment a worker sandbox.

### Full Linux/KVM guest under a restricted service

The official Ubuntu packages `qemu-system-x86` and `qemu-utils` were installed
without recommended GUI packages (QEMU package `1:8.2.2+ds-0ubuntu1.18`, libslirp
`4.7.0-1ubuntu3.1`). The package's KVM preparation service is a oneshot, not an
agent worker daemon. A separate system account with no login shell runs the trial;
KVM group access is granted through the transient service configuration.

The same verified Ubuntu image and nonce-bound offline diagnostic booted under
KVM, using a fresh overlay, no network device and no guest directory shares.
Systemd enforced `User=daia-runtime`, `NoNewPrivileges=yes`, `ProtectSystem=strict`,
`ProtectHome=yes`, inaccessible `/mnt`, a private network namespace and private
temporary directory. Only the job directory was writable through the service's
filesystem policy. Device policy allowed KVM; memory and task limits were 3 GiB
and 64. A live `/proc` comparison confirmed a different network namespace from
the WSL host, alongside the active service properties.

The non-root probe confirmed template write denial and inaccessible `/mnt/c`.
The guest reported only loopback, no shared filesystem and successful checks,
then shut down with exit 0. Systemd reported service success, 2m37.810s runtime,
15.451s CPU and 604.1 MiB peak memory, without swap. These are one diagnostic's
measurements, not a throughput estimate. Independent post-run checks found no
overlay and no active unit main process.

This is a real restricted-service guest boot, not an adversarial escape proof.
The ordinary WSL user environment is not the worker boundary: the guest and its
transient service are. Public egress, provider-account confinement, useful native
agent execution and job/result integration remain release gates. The private
network namespace provides a concrete place to test an explicit gateway channel
without exposing the host network as the worker's default route.

### Linux Unix-socket gateway: repeated requests and controlled loss

A fixed Python stream bridge under the runtime account connects only to one
operator-created Unix socket. The synthetic HTTP server is outside the service's
private network namespace. The guest uses QEMU's restricted user network and
per-connection command forwarding; no ordinary host IP route was added.

The live KVM guest completed three sequential and three parallel connections.
Every response carried its request-specific nonce/index, and the host independently
recorded all six expected paths. A second scenario stopped and removed the Unix
listener after those six responses. The subsequent request failed, and a direct
guest attempt to a separately prechecked live host-loopback canary was refused;
the host confirmed no queued canary connection. The service succeeded and its
overlay was removed.

Initially, an uncaught bridge socket exception appeared as invalid HTTP data.
The bridge now exits silently on socket errors. Repeating the complete loss
scenario retained all six correct responses, then produced `ConnectionResetError`
without a traceback response or direct canary connection. This is a tested transport
fixture, not a public proxy or provider gateway. It has no destination-selection
interface. IPv6, public DNS/redirect checks, TLS/provider restrictions and a useful
native-agent task remain untested.

Some terminated-service memory summaries were implausibly small. An active check
instead read 655,024,128 bytes current and 655,147,008 bytes peak from both systemd
and the kernel cgroup files, with a configured 3 GiB ceiling. The final repeat
reported 624.7 MiB peak. Do not use the earlier small summaries as capacity data;
resource-limit fault injection is a separate acceptance check.

### Resource and watchdog fault injection

Three bounded synthetic processes exercised the Linux service controls, without
running contributed code or touching provider accounts:

- A non-root allocator inside a 64 MiB cgroup with zero swap was killed by the
  kernel. Systemd reported `oom-kill` and signal 9; no main process remained.
- A separate service with `TasksMax=16` started 15 children, then received `EAGAIN`
  for the next fork. The parent cleaned up its children and exited successfully.
  The 64 MiB/zero-swap/16-task values were checked while the service was active;
  querying a collected unit afterward can misleadingly return default limits.
- A two-second watchdog with one-second stop timeout killed both a parent and its
  child despite both ignoring SIGTERM. Systemd reported `timeout` and signal 9;
  independent `/proc` checks found neither process remaining.

These prove the tested cgroup and watchdog mechanisms with small fault fixtures.
They do not prove a full agent stays within its provider budget, filesystem size
limits, or survives/reports every controller failure. The VM trial's configured
3 GiB/64-task profile and its useful-work suitability remain separately measured.
All temporary test services were finished and their failed-state records reset.

### Public HTTPS prerequisite

The [experimental public-egress core](public-egress.md) now has local regression
coverage and a live KVM-to-public-website test through a separate non-root gateway.
It retains the private worker network namespace. See that document for the DNS
isolation fix, exact evidence and the distinction between socket authorization
and provider/account authorization inside opaque TLS. This does not open cutover.

### Dependency installation and separate evaluator fixture (2026-09-13)

Two fresh KVM guests exercised development work through the separate public
CONNECT gateway. The gateway allowed only `pypi.org` and `files.pythonhosted.org`;
neither guest received provider credentials, host mounts or a push credential.
The first fetched pinned pip 25.2 and packaging 25.0 wheels over verified TLS,
checked their SHA-256 against PyPI metadata, bootstrapped pip inside the guest and
installed packaging into a guest-local target with no index or dependency lookup.
These metadata checks bind the download to PyPI's response, not an independent
package-signing authority.

A fixed reference task demonstrated the lexical-version comparison bug, applied
a supplied correction using `packaging.version.Version`, and passed six cases.
Its bounded JSON output contained a single-file unified patch, base digest and
patch digest. The patch SHA-256 was
`bbdbd62044b9025581aea6208db047e10c6f9ae101aede5dce684089a67a8033`.
A second fresh guest received only that fixture artifact and its own seed. It
validated the exact fixture path/hunk and base, independently installed the same
pinned dependency and passed six different cases against the reconstructed patch.
Candidate code was executed only in the evaluator guest, not on the host.

Both non-root runtime probes confirmed inaccessible Windows mounts, immutable
templates, exit zero and removed overlays. Independent post-run checks found
both worker and gateway main PIDs zero, no overlays and no gateway socket. Runs
took about 46 seconds each; the collected-unit memory summary was implausible and
is not used as capacity evidence.

This is a private reference-fixture integration test, not an autonomous agent
contribution or a general patch evaluator. Its patch and correction were supplied
by the maintainer. Native-client authentication, provider-account confinement,
complete egress enforcement and assignment-bound controller integration remain
release gates. No real assignment, consent, identity or admission was changed.

### Real assignment helper across the KVM boundary (2026-09-13)

A fresh non-root KVM guest spoke newline-delimited MCP through the fixed Unix
bridge to the existing assignment-only helper outside the guest. A disposable
coordinator and synthetic invite/identity were used; no admitted contributor or
production database participated. The helper retained the private key, signed job
authority, assignment binding and saved consent outside the VM.

The guest saw exactly `heartbeat` and `submit_result`. Attempts to claim work,
stop participation or register an identity were rejected. After a successful
heartbeat, the test deliberately discarded the first submission response after
the coordinator had committed it. A changed artifact retry was rejected; the
exact original retry returned `already_recorded` and the expected receipt hash.
The coordinator held exactly one result. Independently read helper state retained
the same key, used count, maximum jobs and deadline; pending and lease cleared only
after the exact receipt was recovered.

The guest exited zero in about 45 seconds and its overlay was removed. The fixed
relay transferred only bounded fixture messages and did not offer a selectable
host destination. This extends the earlier namespace test to the actual KVM guest
boundary. The trusted test orchestrator/helper ran outside the guest with elevated
lab access; this is not a production non-root controller implementation. It does
not establish native-agent/provider confinement or HTTPS cohort migration. Those
gates remain closed.

### Non-root assignment signer and bounded relay follow-up

The same KVM receipt-loss scenario was repeated with the helper in a separate
`daia-controller` system account and private filesystem root. The host operating-system tree,
interpreter environment, source and fixed helper entrypoint were bound read-only; its private state was the
only writable persistent binding. The coordinator database remained outside that
root. Both worker and public-gateway accounts were tested against the helper's
state file and could not read it. Live process inspection confirmed a nonzero UID,
zero effective capabilities, no-new-privileges and active seccomp. Systemd was
configured to permit loopback IP traffic for the synthetic local coordinator and
deny other IP traffic; configuration alone does not prove that enforcement.

The guest again exposed only the two assignment tools, refused changed pending
content, recovered the exact recorded receipt and left one coordinator result.
The saved signing key, used count, maximum jobs and deadline were unchanged. The
worker and helper stopped and the overlay and socket were removed.

Review found that early setup failures bypassed cleanup and blocking pipe writes
could delay the relay deadline. The lab harness now registers cleanup before helper
startup and uses nonblocking descriptor queues. The complete guest scenario passed
again. A helper that never consumed stdin caused the real relay to return in 30.03
seconds. An injected setup exception before worker launch left no running helper
or socket. A killed orchestrator cannot run Python cleanup; independent service
runtime limits remain necessary and immediate recovery after SIGKILL is not proven.

The elevated test orchestrator still starts the services and relays their bytes.
The worker process also retains access to some host filesystem Unix sockets through
its service filesystem view; a private network namespace alone does not isolate
those sockets. These are remaining production boundaries, not claims established
by the successful assignment/signing test. Native-agent/provider confinement and
actual cohort cutover remain incomplete.

### Worker filesystem-root and host-socket canary

A subsequent KVM run also placed the host-side worker runtime in its own systemd
`RootDirectory`. It bound only `/usr`, the lab templates and the exact assignment
socket read-only, plus its disposable job directory and KVM device. Private devices
and the private network namespace remained enabled. Live inspection of the running
process root confirmed the assignment socket visible and a separate host control
socket absent.

The control socket was first reached by a separate process under the same runtime
UID outside that root. Inside the worker service, the probe explicitly attempted
the same path and received file-not-found. The host observed no subsequent canary
connection. The full guest MCP sequence still passed: restricted tools, refused
changed pending artifact, exact receipt replay, one result and unchanged identity
and consent. This closes the tested filesystem-socket visibility gap in the earlier
lab service profile; it is not exhaustive host-IPC or hypervisor escape testing.

Review identified an unchecked code insertion in the private harness and an EOF
path that could discard queued relay bytes. The insertion now requires exactly one
match. Relay queues drain before half-closing their destination, and a real pipe/
socket regression passed in both directions. Static re-review found no remaining
blocker in those fixes. The complete rooted KVM/canary scenario passed again with
the corrected relay. Runtime templates are still lab artifacts; packaging, the
remaining root orchestrator/relay, native provider confinement and authorized
HTTPS cohort migration remain separate release work.

### Unprivileged relay process

The repository relay entrypoint was exercised in the KVM assignment fixture under
its own `daia-relay` account, a private filesystem root and private mount/network
namespaces. Only an inherited Unix listener and the helper's two pipe descriptors
were passed; standard input was the null device. The relay neither held a signing
key nor received a helper-launch command. Live inspection confirmed its non-root
UID, zero effective capabilities and no-new-privileges. Filesystem roots for both
helper and worker remained in force.

An initial namespace fork retained duplicate pipe descriptors, and the relay did
not exit after the guest recovered its receipt. Direct execution in the mount/net
namespaces removed the extra parent. The repeated complete scenario passed,
including relay exit, one recorded result, exact receipt recovery and unchanged
identity/consent. The relay does not claim a separate PID namespace in this profile.
Privileged bootstrap still prepares namespaces and starts services; it no longer
handles the worker byte stream. This is a lab integration of the descriptor CLI,
not a complete deployable worker installer or native-provider confinement proof.

Review added explicit refusal of mismatched real/effective GIDs alongside the UID
checks. CLI privilege checks do not replace independent OS isolation and resource
limits installed by the launcher.


### Native Codex transport fixture and independent cleanup check

The native Linux Codex CLI 0.153.4 ran inside the rooted KVM worker with a clean
HOME and CODEX_HOME, no imported credentials, strict configuration and an explicit
custom Responses provider. The tested executable SHA-256 was
`56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da`.
The guest reached only the fixed external Unix-socket bridge. The provider was a
synthetic SSE fixture without external inference or authentication; it returned
one fixed assistant message. The client exited zero and emitted both the exact
expected completed assistant message and a completed turn event.

The external fixture recorded `/v1/responses`, the expected fixture model and no
Authorization header. These observations establish native client transport through
this lab boundary, not genuine model reasoning, tool execution, provider-account
isolation or a completed development task. Guest bootstrap ran as guest root;
the host worker ran under the separate non-root runtime account.

An independent post-run check found both worker and fixture services inactive with
MainPID zero and their transient units unloaded. The writable guest overlay and
connection socket were absent. This verifies normal-run cleanup for this execution;
it does not prove cleanup after every launcher crash. The reported final service
memory sample is not used as a capacity measurement.

Before this route can support cohort cutover, a real native agent must complete the
public development fixture through a narrowly bounded model route. That run must
also demonstrate that account operations and private network destinations remain
unavailable. A local-model run can establish useful agent execution without cloud
credentials, but cannot establish confinement of a subscription account. The
existing synthetic helper migration and receipt tests remain separate evidence;
real admitted identities, finite grants and pending receipts still require explicit
reconciliation during the authorized cutover.


### Native tool execution with the client's sandbox enabled

The native-client fixture was extended to return one fixed shell function call:
write a marker file inside the guest workspace and read it back. The first run
failed because the minimal guest image lacked bubblewrap, required by this Codex
version's Linux sandbox. Copying only the client executable was therefore not a
complete native runtime installation.

The lab image then included the existing bubblewrap executable, verified by hash
before guest installation. The same test passed with `workspace-write` enabled:
the native client emitted a successful command-execution event, the guest checked
the marker file's contents, the synthetic provider received the marker in the tool
result, and the client completed its final turn. The host worker remained non-root
inside its filesystem and network boundaries. Independent post-run inspection
found both transient services inactive, with no guest overlay or connection socket.

This proves a real native tool round-trip through the lab transport, including the
client's own sandbox. The function call was predetermined by the fixture, not
chosen by a real model. No provider credentials or billed inference were used;
useful autonomous development and provider-account confinement remain unverified.


### Withdrawn native network evidence

Adversarial review found that the generated attack server was not selected by the
launcher. Earlier negative and combined-web runs showed a native tool completing,
but did not establish that the intended network assertions ran. Those results are
withdrawn as acceptance evidence. The corrected run below binds the generated
server to the executed bytes and repeats the combined assertions. Cleanup was
also corrected to stop the worker as well as the gateway.

### Corrected native combined probe

After the evidence correction above, the launcher selected the generated attack
server explicitly and compared its staged bytes before starting the gateway. The
server SHA-256 was `00954e7ec7abbd697044d464292dd844febb1e940f735d955f8c9ac0d26619db`.
The corrected run completed the native command and final turn: public HTTPS
returned 200, private CONNECT returned 403, the direct host attempt received an
explicit connection failure, and the host listener saw only its positive control.
The marker is written only after these assertions. No real model credentials were
used. These results supersede the earlier unbound combined-probe claim.

Cleanup now stops both recorded services and removes the overlay after stopping
the worker. Normal completion passed. A deliberate SIGTERM test then confirmed a live QEMU
process, both active services and an existing overlay before signaling the launcher.
The launcher exited nonzero; both services became inactive and the overlay and
gateway socket were absent within 0.32 seconds. These checks preceded the test
driver fallback cleanup. This covers handled interruption, not SIGKILL, power loss
or a controller crash that prevents finally blocks from running. This remains a
bounded lab result, not provider-account isolation or production-cutover acceptance.


### Controller hard-crash cleanup

The lab launcher now attaches fixed ExecStopPost cleanup commands to the worker
and gateway services, in addition to the controller's normal cleanup. A separate
probe confirmed live QEMU, an existing overlay and two active services, then sent
SIGKILL to the controller. Its exit status was -9, so its finally cleanup could not
run. The service manager independently stopped both services and removed the overlay
and socket; assertions passed before the test driver's fallback cleanup.

This probe shortened worker/gateway RuntimeMaxSec to 20/25 seconds, respectively.
Cleanup was observed after 24.11 seconds. Both service journals explicitly recorded
runtime-limit expiry and timeout results. This demonstrates the shortened lab
configuration's independent deadline and cleanup behavior, not a measured result
for the normal 210/240-second settings. It does not test host power loss, reboot
recovery or confidentiality of residual files elsewhere in the lab directory.
The changes are still private lab harness work, not an installed production worker.


### Native Codex with the assignment-bound helper

A combined KVM trial completed using the pinned native Codex client, a synthetic
Responses fixture on guest loopback and the real DAIA assignment MCP helper under
a separate non-root controller identity outside the VM. No provider credentials
or existing contributor state were used. The coordinator and enrollment were
synthetic fixtures. The guest MCP adapter maintained one fixed connection through
the existing unprivileged assignment relay.

The native client discovered the heartbeat and submit_result tools in the actual
MCP namespace. Explicit per-tool approval was configured only for those two tools
in the disposable guest, using the documented
[approval override](https://learn.chatgpt.com/docs/config-file/config-reference).
The model fixture issued a heartbeat and a candidate submission. The helper then
injected response loss after the coordinator committed the result. A changed retry
was rejected; the exact original retry returned already_recorded. Because native
MCP output hides the specific exception behind a generic error, the trusted helper
independently recorded and checked both expected error reasons and retained pending
state. Generic model-visible errors alone were not counted as proof.

The receipt hash reported through native MCP equaled the helper's saved receipt.
The coordinator held exactly one result; helper key, used count, deadline and job
limit equaled their pre-execution values. Pending and lease cleared only after the
exact receipt. Native execution and its final turn completed successfully. Other
service identities could not read helper state; the host socket canary remained
hidden from the rooted worker despite a successful outside-worker positive control.
The worker and helper were independently observed inactive after completion, with
no guest overlay or gateway socket.

An initial 64-task host cgroup exhausted QEMU threads. The successful combined
trial used TasksMax=128; this is a bounded lab setting, not a production capacity
measurement. This trial establishes native-client/helper integration for the
prepared task and retry sequence. It does not establish autonomous model quality,
provider-account confinement, preservation of a real participant identity during
cutover, or a supported production installer. The executable harness remains
private lab work and still needs a reproducible repository integration.

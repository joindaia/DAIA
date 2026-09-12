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

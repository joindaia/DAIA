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
Standard output is untrusted task output. Input screening is not a secret detector.
Do not use this primitive alone as evidence that the full worker gate has passed.

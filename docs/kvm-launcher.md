# Restricted KVM launch component

Status: experimental component, not a participant installer. This extracts the
fixed three-relay KVM boot path from private lab code. It does not install service
identities, create an approved task, perform login, or start the external helper,
research and model services. Those parts of the full launcher remain to package.

[`run_kvm_lab_guest.py`](../scripts/run_kvm_lab_guest.py) must run in an externally
supervised, nonroot Linux service with a loopback-only private network namespace,
KVM access and a fresh private working directory. There is no software emulation
or host-execution fallback. It uses two CPUs, 2 GiB guest memory, a 180-second
QEMU timeout, no host mounts, no monitor, no display and restricted user networking
with exactly the assignment/model/research guest-forward routes on 100/101/102.

The trusted installer must make the bundle and its ancestors immutable to the
runtime identity and prevent concurrent replacement. Read-only files and matching
hashes do not authenticate a manifest supplied by a worker. An operator-approved
manifest and all its executable bridge bytes must be installed outside task
control. The script itself belongs to the separately approved runtime bundle.

The bundle contains:

- `base.qcow2`: approved base image.
- `network-seed.iso`: approved assignment-specific guest seed.
- `bridge.py`, `model-bridge.py`, `research-bridge.py`: the three fixed relays.
- `network-config.json`: `nonce` (32 lowercase hexadecimal characters),
  `base_sha256`, `seed_sha256` and `bridge_sha256` mapping exactly the three bridge
  filenames to their SHA-256 digests.

Every referenced file must be regular, non-symlink and not writable by the runtime
identity. Digests are streamed before creating the overlay or starting QEMU.
Missing files, unknown manifest fields, missing bridge pins or a mismatched digest
stop startup. Paths are limited to managed absolute paths without QEMU/shell
separator characters. The manifest is trusted configuration, never guest input.

Example service command, **only after configuring the required outer boundary**:

```sh
/usr/bin/python3 -I /opt/daia/scripts/run_kvm_lab_guest.py \
  --bundle /var/lib/daia-worker/bundles/approved
```

Keep the already-tested outer restrictions: separate runtime identity, no personal
home or Windows mounts, read-only system/bundle, cleared credentials/environment,
KVM-only device access, memory/process limits and an independent runtime watchdog.
The supervisor must remove the overlay even when this script is killed; its
`finally` clause covers ordinary failures, not SIGKILL. Also bound filesystem
usage externally: the post-run 8 MiB serial-size check bounds parsing, not how much
an actively running guest can write to disk. This is an unresolved installation
gate, not a claim that whole-worker disk quotas are installed. The subsequent
[bounded storage trial](worker-storage.md) verifies a service-private work quota;
other writable paths and full supervisor integration remain open.

The private `report.json` contains the guest's correlated output. A matching nonce
only establishes correlation. `guest_claims_verified: false` is deliberate; the
controller must separately verify receipts, artifacts and test outcomes. Only a
small trusted startup summary is printed, not arbitrary guest output.

## Validation

The real Linux/KVM component trial checks a wrong bridge pin first, requiring
failure before any work-directory file is created. The valid bundle then boots a
credential-free guest and removes its overlay. This tests startup and hashing,
not the three relays, provider login, model execution or broad worker safety.
See the [measured result](research/packaged-kvm-launch-2026-09-13.json).


## Bridge backpressure prerequisite

The repository's `model_channel_bridge.py` now uses nonblocking socket and pipe
writes. Its previous synchronous stdout write could block beyond the nominal
30-second deadline when QEMU stopped reading. The revised relay limits total
bidirectional transfer to 16 MiB, applies backpressure to bounded directional
queues and checks its deadline even when a destination never becomes writable.
Unix connection setup has a five-second timeout. Upstream upload rejection still
allows the reply to drain; a disconnected output consumer ends the bridge.

Real socket/pipe tests cover stalled upload, stalled download, early HTTP rejection
and excess bytes. Together with the assignment relay suite: 12 passed on Linux.
This changes the repository bridge, not immutable prepared lab bundles. Those
must be rebuilt, pinned and tested before the complete launcher can use it; no
new live-subscription or KVM result is asserted for this revision.


## Bounded bridges in the real KVM lab

The [follow-up run](research/bounded-bridge-kvm-2026-09-13.json) rebuilt the three
lab bridge files from `model_channel_bridge.py` at `122e24c`. The only source
substitution was the fixed Unix destination: assignment uses
`/run/daia-lab/gateway.sock`, model uses `/run/daia-lab/model.sock`, and research
uses `/run/daia-research/gateway.sock`. No worker-selected destination was added.
Exact bridge SHA-256 values are retained in the report.

From the real guest, assignment MCP initialization succeeded, a forbidden model
route returned HTTP 403, and the research gateway allowed controlled public-IP
canaries but refused the same names after actual DNS answers changed to loopback,
for both IPv4 and IPv6. The external receiver observed 20 positive control
connections and zero unexpected private connections. This uses the existing
DNS-rebinding guest/server fixtures, not public provider credentials.

After SIGKILL of the parent controller, all five cgroups became empty, all three
sockets became unreachable and the overlay/temporary credential handoffs were
removed in 0.053 seconds. Python exit cleanup did not run. This verifies the new
bridges within the existing lab boundary; it does not package that boundary or
repeat a full subscription development/receipt workflow.


## Offline bundle assembly

`prepare_kvm_bundle.py` assembles the approved base and seed plus the repository's
launcher and three fixed bridges. Supply independently approved base/seed SHA-256
values, the task's correlation nonce and a new output directory. It hashes copied
bytes, refuses input symlinks and existing output, and removes its own incomplete
directory on failure. No source file is executed, downloaded or linked to mutable
input. The output files become read-only; the printed hash list includes the
launcher as well as every other file, without source paths or credentials.

```sh
python scripts/prepare_kvm_bundle.py \
  --base "$APPROVED_BASE" --base-sha256 "$BASE_SHA256" \
  --seed "$APPROVED_SEED" --seed-sha256 "$SEED_SHA256" \
  --nonce "$ASSIGNMENT_NONCE" --output "$NEW_BUNDLE"
```

Identical inputs and repository scripts produce identical file bytes/hashes. This
is assembly of existing approved artifacts, not reproducible compilation of the
base image or client, seed generation, or a signed release. The trusted installer
must approve the builder/scripts and output, protect ancestor directories and keep
untrusted code out of the installation identity. Hashes supplied by a worker do
not constitute approval. Do not activate partially built directories.

The offline test checks identical assemblies, bridge destinations, read-only files,
refusal to overwrite existing output, pin mismatch cleanup and symlink refusal.


The first real assembled-bundle trial passed input verification but failed during
QEMU execution. The service reported exit status 1; the precise QEMU cause was
not retained because its private diagnostic file disappeared with the work mount.
See the [failed trial record](research/assembled-kvm-bundle-2026-09-13.json).
This is an unresolved integration failure, not a passing boot result. The next
trial must retain bounded private failure diagnostics before teardown while
preserving storage, network and watchdog limits.


### Follow-up: explicit internal guest networking

The unchanged assembled bundle subsequently booted successfully on repetition with
bounded diagnostic inspection. Its initial QEMU failure remains unexplained. Live
serial output showed over 100 seconds waiting for `systemd-networkd-wait-online`;
the initial fixture had an empty ethernet definition.

The [checked-in seed inputs](../tests/fixtures/kvm-boot-seed/) now configure a fixed
`10.0.2.15/24` address, disable DHCPv4/v6 and mark the matched guest NIC optional.
No default route or external DNS server is added. This is a synthetic boot fixture,
not a participant task or permission to use these settings on the host.
Generate a cidata ISO from its `user-data`, `meta-data` and `network-config`, then
supply that ISO's approved digest and the fixture nonce to the offline builder.
ISO timestamps can change its bytes: reproducible bundle assembly applies to
identical ISO input, not regeneration by an unpinned ISO tool invocation.

A fresh bundle built from these inputs completed the same restricted KVM/storage
trial in 44.899 seconds, including launch/teardown overhead. All four mount limits
held, the overlay was removed and the underlying host directory stayed empty.
[Exact hashes and results](research/assembled-kvm-static-network-2026-09-13.json)
are recorded. No model credentials or requests were used. This removes the empty
network configuration from the fixture; it does not prove the original failure's
cause or close full participant-installation acceptance.


## Capturing failure before teardown

The bundle now includes `report-wrapper.py`, assembled from
`run_kvm_lab_report.py`. Inside the same restricted service, invoke it with the
approved `--bundle` path instead of invoking `launcher.py` directly. The wrapper
executes that launcher and emits an `ok` envelope. On success, `report` contains
the existing untrusted guest report; on failure, `untrusted_diagnostics` contains
at most the final 4096 bytes each of QEMU stderr and serial output, decoded as text.
The controller must capture this JSON in private storage before destroying mounts,
never display it as terminal commands or treat it as trusted instructions.
Exit status stays nonzero on failure; bounded diagnostics do not convert failure
into success. The same independent service watchdog remains mandatory.

A unit/process test confirms a failing launcher with 20,000 serial bytes exports
only 4096 bytes. Bundle assembly includes and hashes the wrapper. This wrapper is
not yet proven in the full live subscription route.

The first assembled subscription trial reached real model requests and native
credential refresh, but ended without the required guest correlation result.
Cleanup removed supervised sockets and handoffs. That is a failed end-to-end
trial, not a completed development task; no independent evaluation was possible.
The private audit reported three forwarded requests, four attempts and 24 refusals,
with credential rotation and the original deadline preserved. The next trial must
use the bounded wrapper to retain guest failure context. Earlier successful
subscription results remain separate evidence from this failed integration.


## Successful assembled subscription trial

A subsequent run used the offline builder, all three bounded bridges, the report
wrapper and the four service-private storage mounts for the original Codex client
with the participant's subscription. It completed four provider requests, native
credential refresh/restart and one DAIA result. Twenty-three negative model-channel
requests were refused. Original identity/consent and the model deadline remained
unchanged; exact retry recovered the receipt and a changed retry was refused.
The controller captured the result before mount destruction and its underlying
work directory remained empty. Supervised sockets/handoffs and the overlay were
removed. The [record](research/assembled-subscription-success-2026-09-13.json)
contains all eight bundle file hashes and the candidate digest.

The coordinator-stored source matched the worker output exactly. A fresh evaluator
with no NIC or provider credentials passed the same ten regression cases on those
unchanged source bytes; the original version failed. This verifies a useful task
through the assembled components, not a clean participant installation: controller
services, native authentication setup and task-seed generation still use lab code.
Submission remains harness-driven. Earlier failed trials remain unexplained.

Failure export additionally scans at most 8 MiB of serial data and retains up to
8 KiB of selected error context, capped per line, so shutdown messages do not
necessarily displace an earlier native failure. This output remains untrusted and
private. Synthetic tests verify retention after 20,000 bytes of later chatter.


## Repository-native authentication lifecycle probe

`probe_codex_native_auth.py --binary "$APPROVED_CODEX" --home "$PRIVATE_AUTH_HOME"`
now reproduces the trusted-side native refresh/restart check without hardcoded
personal paths. The existing dedicated profile must be owned by the invoking user,
private, and nonsymlink; the client must match the pinned 0.153.4 SHA-256. This
probe runs outside the worker and must never be exposed as a worker tool.

It sends only native initialization and `account/read`, requesting refresh in the
first process and reading persisted state in a fresh second process. Each response
has a 45-second deadline and 1 MiB aggregate byte limit. RPC errors withhold their
payloads. The process environment contains only PATH and the dedicated HOME/
CODEX_HOME; credentials are compared privately and only booleans are reported.
Success requires token rotation on the first run, no further token change on the
second, unchanged account, private auth file and clean client exits.

The live run observed all those properties, with zero requested model calls and
no worker started. Two negative preflight tests confirm an incorrect binary or
symlink is rejected before execution and leaves a synthetic auth file untouched.
This packages the lifecycle probe, not the initial interactive login, an external
identity proof, provider revocation, or the complete production credential broker.


## Repository-native subscription lab controller

`run_subscription_lab.py` now supervises `run_subscription_lab_controller.py`
from the checkout. The assignment helper and public-research service are also
repository files. Native authentication invokes `probe_codex_native_auth.py` as
the existing dedicated profile owner, with a cleared environment; it does not
request a new login. The former private controller scripts are not needed by this
entry point.

On the already configured, dedicated Linux lab host, supply trusted operator paths:

```sh
sudo python3 scripts/run_subscription_lab.py \
  --guest "$APPROVED_GUEST_FIXTURE" \
  --request-template "$APPROVED_NATIVE_REQUEST" \
  --auth-home "$DEDICATED_PRIVATE_PROFILE" \
  --codex-binary "$PINNED_NATIVE_CODEX" \
  --python-runtime "$APPROVED_PYTHON_RUNTIME"
```

The guest directory must contain the existing approved `seed.iso`, `config.json`
and `probe.py`. The runtime needs the repository's development/MCP dependencies.
Four restricted lab users, KVM, the pinned base image and lab directories must
already exist. The controller never creates accounts or logs a participant in.
Inputs and this checkout are trusted administrator code, not worker-controlled.

The supervisor holds an exclusive process lock because templates are shared,
refuses existing endpoints, removes the previous result before starting, and
creates an independent 210-second systemd limit with explicit credential-handoff
and socket cleanup. Child services are bound to that parent. Existing model
limits remain six requests and 150 seconds. No broader consent is requested.

This remains an experimental lab route, not a clean-machine installer or a
production authority boundary around the administrator. Task-seed generation,
initial authentication setup and the independent evaluator still require lab
preparation. Submissions are harness-driven. The profile, request template,
private reports and task seed are not published.

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

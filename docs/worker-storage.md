# Bounded worker storage

Status: tested storage primitive and credential-free KVM work-directory trial;
not yet complete worker storage confinement or an installed production profile.

Use a service-private `TemporaryFileSystem` for the disposable work directory.
The kernel enforces both byte and inode limits independently of guest/model
behavior. It disappears with the service mount namespace; the underlying host
directory is not the worker's backing store. Keep swap disabled and budget tmpfs
pages together with QEMU memory in the service cgroup.

The [standalone credential-free probe](../scripts/probe_worker_storage.py) uses an
existing `daia-runtime` account, 16 MiB and 64 inodes. It checks the actual mount
and filesystem limits before attempting to fill anything. Observed ENOSPC at
16,777,216 written bytes and after 63 empty files (one inode belongs to the root
directory). Removing those files restores normal writes. A direct executable on
the noexec mount is refused. This is not a ban on interpreting scripts: Python
can still read code as data, and hostile code remains inside the execution VM.

A real KVM boot uses the extracted launcher with a 512 MiB / 4096-inode work
mount, 3 GiB service memory ceiling, swap disabled and the same external watchdog.
The trusted in-service wrapper reads the correlated report before namespace
teardown. The [KVM storage driver](../scripts/probe_kvm_storage.py) accepts the trusted
prepared boot-test bundle through `--bundle`. See the [measured results](research/worker-storage-2026-09-13.json).
This boot fixture does not use model credentials or exercise subscription flows.

The tested work-mount options are `size=512M,nr_inodes=4096,mode=0700`, the numeric
UID/GID of the restricted runtime user, and `nodev,nosuid,noexec`. Resolve that
identity during trusted installation; do not hardcode a machine-specific UID.
The outer directory is prepared for the runtime identity. An initial probe failed
with `200/CHDIR`; correcting ownership and removing a redundant `ReadWritePaths`
bind for the same path produced the successful configuration. Do not blindly
combine writable host bind mounts with the temporary work mount.

## Remaining integration

- Apply the policy in the packaged supervisor, not only a test service. Choose
  byte/inode budgets before assignment execution and keep the memory ceiling
  large enough for the approved guest plus temporary pages, without swap fallback.
- Inventory and bound every other writable location, including private temporary
  directories and shared-memory mounts. A work-directory quota alone is not a
  whole-worker host-storage limit. Guest-owned paths inside the qcow2 overlay
  consume that overlay; host-side QEMU/bridge paths require separate treatment.
- Export only bounded result bytes before teardown. The host cannot read the
  service-private `report.json` afterward. Preserve helper/receipt recovery state
  outside the guest work mount, without exposing it to task code.
- Test forced controller/worker death and recovery with this storage layout.
  Normal service exit and an unchanged underlying host directory do not alone
  establish every crash, leaked namespace or orphan-process scenario.

The probe performs no provider requests, changes no production configuration and
creates no persistent mounts. It requires the trusted lab administrator only to
create the restricted test service; the write probe itself is nonroot.

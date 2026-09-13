# Bounded worker storage

Status: tested storage primitive and credential-free KVM work-directory trial;
not yet complete worker storage confinement or an installed production profile.
The subsequent four-filesystem trial below extends the work-directory baseline.

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
- Integrate the four explicit bounded mounts and inventory remaining writable
  mounts, device and IPC paths. Even these four quotas are not by themselves a
  whole-worker host-storage proof. Guest-owned paths inside the qcow2 overlay
  consume that overlay; host-side QEMU/bridge paths require separate treatment.
- Export only bounded result bytes before teardown. The host cannot read the
  service-private `report.json` afterward. Preserve helper/receipt recovery state
  outside the guest work mount, without exposing it to task code.
- Integrate full assignment and pending-result recovery with this storage layout.
  The forced service-death trial below covers process and temporary-storage cleanup,
  not restored task execution or every leaked-namespace scenario.

The probe performs no provider requests, changes no production configuration and
creates no persistent mounts. It requires the trusted lab administrator only to
create the restricted test service; the write probe itself is nonroot.


## Extended temporary/shared-memory coverage

The updated standalone probe creates separate bounded mounts for work, `/tmp`,
`/var/tmp` and `/dev/shm`. All four have distinct filesystem device identifiers,
and each independently reaches ENOSPC at 16 MiB and 63 created files, recovers
normal writes after deletion and refuses direct execution. Unique synthetic host
canaries in the three fixed host locations are absent inside the service and
unchanged afterward. Actual kernel mount and limit checks precede all filling.

The KVM trial keeps the 512 MiB/4096-inode work mount and adds separate 16 MiB/
256-inode mounts for `/tmp`, `/var/tmp` and `/dev/shm`, using the runtime UID/GID
and `nodev,nosuid,noexec`. `PrivateIPC=yes` is configured. `PrivateTmp` is replaced
by explicit temporary-filesystem mounts rather than an unbounded private host
storage directory. This controls host-side QEMU/helper scratch space; guest paths
remain inside the qcow2 overlay. The same real credential-free guest boots and
reports successfully, its overlay is removed and the underlying host directory
remains unchanged. See the [extended results](research/worker-storage-extended-2026-09-13.json).

This trial does not claim complete IPC isolation, cover every writable kernel
interface, or establish forced-crash recovery. It also does not rerun a real
subscription or arbitrary dependency-installation task with this storage profile.


## Forced service death and fresh storage

The [crash probe](../scripts/probe_storage_crash.py) uses the same trusted boot
bundle and four bounded mounts. It waits for the matching guest boot result,
checks that a real QEMU process is still running and that synthetic state exists
in all four mounts, then sends SIGKILL to the service main process. The service
manager removes the remaining processes without relying on Python cleanup.

In the [observed run](research/worker-storage-crash-2026-09-13.json), the cgroup
became empty and every recorded process disappeared in 0.064 seconds. The
underlying host work directory stayed empty. A new service with the same storage
profile found four empty, distinct filesystems and successfully wrote fresh data.

This is a fresh service test, not a second VM boot or a resumed DAIA assignment.
It uses no credentials or model requests. Full assignment/receipt recovery,
provider binding cleanup and a useful task under the packaged storage profile
remain integration requirements.


## Pending-result persistence before retry

The contributor now saves pending state before every submission attempt, including
exact retries. Previously, a failed pending-state write could leave the signed
submission only in memory. Normal recovery saves state, but recovery that ignores
an unsolicited different assignment returns early; a retry along that path could
reach submission without a successful pending-state write.

The regression injects persistent storage failure and an unrelated recovered
assignment. Both attempts must fail before submission; after storage recovers,
exactly one result is accepted and pending state clears. The test fails against
the previous implementation at the outbound submission boundary (disk pending is
null while memory contains the result), and passes with the fix. Relevant local
suite: 51 passed, two Windows-specific tests skipped. This does not establish
power-loss durability or replace full VM/assignment recovery integration.

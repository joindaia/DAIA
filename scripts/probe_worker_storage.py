"""Credential-free Linux test of a service-private bounded work filesystem.

Run as root in the dedicated DAIA lab with an existing daia-runtime user.
Only the inside probe writes data, under that restricted service identity.
This is a storage/lifecycle probe, not a complete worker installer.
"""
import argparse
import errno
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
import tempfile
import uuid

LIMIT = 16 * 1024 * 1024


def inside():
    work = Path.cwd()
    assert os.getuid() != 0
    # Refuse to fill a directory unless the kernel actually mounted our limit.
    mounts = Path('/proc/self/mountinfo').read_text().splitlines()
    assert any(line.split()[4] == str(work) and ' - tmpfs ' in line for line in mounts)
    stat = os.statvfs(work)
    assert 0 < stat.f_blocks * stat.f_frsize <= LIMIT
    assert 0 < stat.f_files <= 64
    data = work / 'fill'
    written = 0
    try:
        with data.open('wb', buffering=0) as out:
            for _ in range(64):
                written += out.write(b'x' * (1024 * 1024))
            raise AssertionError('Byte limit was not enforced')
    except OSError as exc:
        assert exc.errno == errno.ENOSPC
    assert 0 < written <= LIMIT
    data.unlink()
    count = 0
    try:
        for i in range(128):
            (work / str(i)).touch(exist_ok=False); count += 1
        raise AssertionError('Inode limit was not enforced')
    except OSError as exc:
        assert exc.errno == errno.ENOSPC
    assert 0 < count <= 64
    for path in work.iterdir():
        path.unlink()
    probe = work / 'normal'
    probe.write_bytes(b'bounded-storage-control')
    assert probe.read_bytes() == b'bounded-storage-control'
    script = work / 'executable'
    script.write_text('#!/bin/sh\nexit 0\n'); script.chmod(0o700)
    try:
        subprocess.run([str(script)], check=True, timeout=2)
    except PermissionError:
        pass
    else:
        raise AssertionError('Work mount should be noexec')
    print(json.dumps({'byte_limit': LIMIT, 'enospc_after_bytes': written,
                      'inode_limit': stat.f_files, 'enospc_after_files': count,
                      'normal_write_after_cleanup': True, 'direct_execution_denied': True}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inside', action='store_true')
    args = parser.parse_args()
    if args.inside:
        inside(); return
    if sys.platform != 'linux' or os.getuid() != 0:
        raise SystemExit('Run the outer fixture as the trusted Linux lab administrator')
    account = pwd.getpwnam('daia-runtime')
    # Keep the executable outside the noexec work mount, readable but immutable
    # to the runtime user. Neither location contains credentials or task data.
    with tempfile.TemporaryDirectory(prefix='daia-storage-probe-', dir='/run') as temp:
        root = Path(temp); root.chmod(0o755)
        script = root / 'probe.py'; script.write_bytes(Path(__file__).read_bytes()); script.chmod(0o444)
        work = root / 'work'; work.mkdir(mode=0o700); os.chown(work, account.pw_uid, account.pw_gid)
        unit = 'daia-storage-probe-' + uuid.uuid4().hex
        options = f'size={LIMIT},nr_inodes=64,mode=0700,uid={account.pw_uid},gid={account.pw_gid},nodev,nosuid,noexec'
        props = {'User': 'daia-runtime', 'Group': str(account.pw_gid),
                 'WorkingDirectory': str(work), 'TemporaryFileSystem': str(work)+':'+options,
                 'ProtectSystem': 'strict', 'ProtectHome': 'yes', 'PrivateTmp': 'yes',
                 'PrivateNetwork': 'yes', 'NoNewPrivileges': 'yes',
                 'CapabilityBoundingSet': '',
                 'MemoryMax': '64M', 'MemorySwapMax': '0', 'TasksMax': '16',
                 'RuntimeMaxSec': '20', 'TimeoutStopSec': '2', 'KillMode': 'control-group'}
        command = ['systemd-run', '--quiet', '--wait', '--pipe', '--collect', '--unit='+unit]
        for key,value in props.items():
            command += ['-p', key+'='+value]
        try:
            result = subprocess.run(command+['/usr/bin/python3', '-I', str(script), '--inside'],
                                    capture_output=True, timeout=30)
            if result.returncode:
                raise RuntimeError(result.stderr.decode(errors='replace')[-2000:])
            report = json.loads(result.stdout)
            assert not any(work.iterdir())
            report.update(service_exit=0, host_work_directory_unchanged=True,
                          credentials_used=False, model_requests=0)
            print(json.dumps(report))
        finally:
            subprocess.run(['systemctl','stop',unit],capture_output=True,timeout=5)


if __name__ == '__main__':
    main()

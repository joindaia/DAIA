"""Run an approved evaluator bundle in the existing restricted Linux lab.

No service/account installation, provider access or model gateway is performed.
The operator supplies an approved read-only bundle and an exclusive result path.
Guest reports remain untrusted. This is a lab entrypoint, not a participant installer.
"""
import argparse
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import uuid


def properties(work, worker):
    def mount(size, inodes):
        return (f'size={size},nr_inodes={inodes},mode=0700,uid={worker.pw_uid},'
                f'gid={worker.pw_gid},nodev,nosuid,noexec')
    mounts = str(work) + ':' + mount('512M', 4096)
    mounts += ' ' + ' '.join(p + ':' + mount('16M', 256)
                             for p in ('/tmp', '/var/tmp', '/dev/shm'))
    return {'User': 'daia-runtime', 'Group': str(worker.pw_gid),
            'SupplementaryGroups': 'kvm', 'WorkingDirectory': str(work),
            'TemporaryFileSystem': mounts, 'NoNewPrivileges': 'yes',
            'ProtectSystem': 'strict', 'ProtectHome': 'yes', 'InaccessiblePaths': '/mnt',
            'PrivateNetwork': 'yes', 'PrivateIPC': 'yes', 'DevicePolicy': 'closed',
            'DeviceAllow': '/dev/kvm rw', 'CapabilityBoundingSet': '',
            'MemoryMax': '3G', 'MemorySwapMax': '0', 'TasksMax': '64',
            'RuntimeMaxSec': '210', 'TimeoutStopSec': '5', 'KillMode': 'control-group',
            'Restart': 'no'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Preconfigured lab administrator required')
    for path in (args.bundle, args.output):
        if not path.is_absolute() or not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(path)) or '..' in path.parts:
            parser.error('Managed absolute path required')
    if args.bundle.is_symlink() or not args.bundle.is_dir():
        parser.error('Approved regular bundle directory required')
    worker = pwd.getpwnam('daia-runtime')
    root = Path('/var/lib/daia-lab')
    unit = 'daia-evaluator-' + uuid.uuid4().hex
    work = root / unit
    work.mkdir(mode=0o700); os.chown(work, worker.pw_uid, worker.pw_gid)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    command = ['systemd-run', '--quiet', '--unit=' + unit, '--wait', '--pipe']
    for key, value in properties(work, worker).items():
        command += ['-p', key + '=' + value]
    command += ['/usr/bin/python3', '-I', str(args.bundle / 'report-wrapper.py'),
                '--bundle', str(args.bundle), '--network-none']
    print(json.dumps({'unit': unit}), flush=True)
    try:
        with os.fdopen(fd, 'wb') as output:
            result = subprocess.run(command, stdout=output, stderr=subprocess.DEVNULL, timeout=225)
        if args.output.stat().st_size > 10 * 1024 * 1024:
            raise ValueError('Oversized evaluator report')
        if result.returncode:
            raise RuntimeError('Evaluator failed; bounded private report retained')
        envelope = json.loads(args.output.read_bytes())
        if not envelope.get('ok') or not envelope['report'].get('network_none'):
            raise ValueError('Expected networkless evaluator report')
        print(json.dumps({'evaluator_completed': True}))
    finally:
        subprocess.run(['systemctl', 'stop', unit], capture_output=True, timeout=15)
        state = subprocess.run(['systemctl', 'is-active', unit], capture_output=True, text=True)
        if state.stdout.strip() in ('active', 'activating', 'deactivating'):
            raise RuntimeError('Evaluator cleanup not confirmed')
        if any(work.iterdir()):
            raise RuntimeError('Evaluator storage survived service teardown')
        work.rmdir()
        subprocess.run(['systemctl', 'reset-failed', unit], capture_output=True)
        print(json.dumps({'private_storage_removed': True}), flush=True)


if __name__ == '__main__':
    main()

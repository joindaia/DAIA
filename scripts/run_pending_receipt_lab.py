"""Recover one existing lab receipt in a bounded non-root private service.

The existing coordinator must already be available at the saved loopback endpoint.
No worker, model, login, new assignment or consent renewal is started. This is a
trusted lab administrator entrypoint, not a worker capability or an installer.
"""
import argparse
import os
from pathlib import Path
import pwd
import re
import subprocess
import tempfile
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('invite', 'authority', 'python-runtime'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--assignment', required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or not re.fullmatch('[a-f0-9]{32}', args.assignment):
        parser.error('Lab administrator and exact assignment required')
    for path in (args.invite, args.authority, args.python_runtime):
        if (not path.is_absolute() or path.is_symlink() or not path.exists()
                or not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(path))
                or '..' in path.parts):
            parser.error('Existing trusted absolute lab paths required')
    if not args.invite.is_file() or not args.authority.is_file():
        parser.error('Existing invite and authority files required')
    owner = pwd.getpwuid(args.invite.stat().st_uid)
    if owner.pw_name != 'daia-controller':
        parser.error('Dedicated lab controller identity required')
    repo = Path(__file__).resolve().parents[1]
    unit = 'daia-receipt-recovery-' + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='recovery-root-', dir='/var/lib/daia-lab') as directory:
        jail = Path(directory); jail.chmod(0o755)
        for name in ('usr', 'opt/runtime', 'opt/source', 'state', 'tmp'):
            (jail / name).mkdir(parents=True, exist_ok=True)
        (jail / 'opt/authority.json').touch()
        for name, target in [('lib', 'usr/lib'), ('lib64', 'usr/lib64'), ('bin', 'usr/bin')]:
            (jail / name).symlink_to(target)
        command = ['systemd-run', '--quiet', '--wait', '--pipe', '--collect',
                   '--unit=' + unit, '--setenv=PYTHONPATH=/opt/source']
        properties = {
            'RootDirectory': str(jail),
            'BindReadOnlyPaths': '/usr ' + str(args.python_runtime) + ':/opt/runtime ' +
                str(repo / 'src') + ':/opt/source ' + str(args.authority) + ':/opt/authority.json',
            'BindPaths': str(args.invite.parent) + ':/state',
            'User': owner.pw_name, 'Group': str(owner.pw_gid), 'WorkingDirectory': '/state',
            'ProtectSystem': 'strict', 'ProtectHome': 'yes', 'InaccessiblePaths': '/mnt',
            'PrivateTmp': 'yes', 'PrivateDevices': 'yes', 'NoNewPrivileges': 'yes',
            'CapabilityBoundingSet': '', 'ReadWritePaths': '/state',
            'RestrictAddressFamilies': 'AF_INET AF_UNIX',
            'IPAddressDeny': 'any', 'IPAddressAllow': 'localhost',
            'RuntimeMaxSec': '20', 'TimeoutStopSec': '3', 'KillMode': 'control-group',
            'MemoryMax': '256M', 'MemorySwapMax': '0', 'TasksMax': '32',
        }
        for name, value in properties.items():
            command += ['-p', name + '=' + value]
        bootstrap = ("from pathlib import Path; import daia.contributor as m; "
                     "assert Path(m.__file__).is_relative_to('/opt/source/daia'), "
                     "'Wrong recovery implementation'; m.main()")
        command += ['/opt/runtime/bin/python', '-c', bootstrap,
                    '--invite', '/state/' + args.invite.name,
                    '--job-authority', '/opt/authority.json',
                    '--recover-pending', args.assignment]
        try:
            result = subprocess.run(command, stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=30)
            if result.returncode != 0:
                print('Receipt recovery refused or failed; no new work requested.')
                return 1
            if result.stdout != b'DAIA pending receipt recovered.\n':
                raise RuntimeError('Unexpected recovery output')
            print('DAIA pending receipt recovered.')
            return 0
        finally:
            subprocess.run(['systemctl', 'stop', unit], capture_output=True, timeout=10)


if __name__ == '__main__':
    raise SystemExit(main())

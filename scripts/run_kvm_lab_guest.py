"""Run a pinned lab guest under an externally supervised restricted service.

Trusted launcher input only. Requires nonroot identity, a private network
namespace containing only loopback, KVM, read-only approved bundle files and an
empty private working directory. The launcher still owns filesystem confinement,
credential separation, cgroups and crash cleanup. No host-execution fallback.
Guest output is untrusted; a matching nonce is correlation, not verification.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys


BRIDGES = ('bridge.py', 'model-bridge.py', 'research-bridge.py')


def checked_path(value):
    path = Path(value)
    if not path.is_absolute() or not re.fullmatch(r'/[A-Za-z0-9_./-]+', str(path)):
        raise ValueError('Managed absolute path required')
    if '..' in path.parts or path.is_symlink():
        raise ValueError('Ambiguous bundle path')
    return path


def verify_bundle(bundle):
    config_path = bundle / 'network-config.json'
    if config_path.is_symlink() or os.access(config_path, os.W_OK):
        raise ValueError('Manifest must be read-only')
    config = json.loads(config_path.read_bytes())
    if set(config) != {'nonce', 'base_sha256', 'seed_sha256', 'bridge_sha256'}:
        raise ValueError('Incomplete bundle manifest')
    if not isinstance(config['nonce'], str) or not re.fullmatch('[0-9a-f]{32}', config['nonce']):
        raise ValueError('Invalid correlation nonce')
    if not isinstance(config['bridge_sha256'], dict) or set(config['bridge_sha256']) != set(BRIDGES):
        raise ValueError('All three bridges must be pinned')
    pins = {'base.qcow2': config['base_sha256'],
            'network-seed.iso': config['seed_sha256'], **config['bridge_sha256']}
    for name, digest in pins.items():
        path = bundle / name
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
            raise ValueError('Invalid digest')
        if path.is_symlink() or not path.is_file() or os.access(path, os.W_OK):
            raise ValueError('Bundle file must be read-only and regular')
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                raise ValueError('Bundle digest mismatch')
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--network-none', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'linux' or os.getuid() == 0:
        raise ValueError('Restricted nonroot Linux service required')
    if {name for _, name in socket.if_nameindex()} != {'lo'}:
        raise ValueError('Private loopback-only network namespace required')
    if not Path('/dev/kvm').is_char_device():
        raise ValueError('KVM required')
    bundle, work = checked_path(args.bundle), checked_path(str(Path.cwd()))
    if any(work.iterdir()):
        raise ValueError('Fresh private working directory required')
    config = verify_bundle(bundle)
    disk = work / 'guest.qcow2'
    try:
        subprocess.run(['/usr/bin/qemu-img', 'create', '-q', '-f', 'qcow2',
                        '-F', 'qcow2', '-b', str(bundle / 'base.qcow2'), str(disk)],
                       check=True, timeout=10)
        forwards = ','.join(f'guestfwd=tcp:10.0.2.{100+i}:3128-cmd:/usr/bin/python3 -I {bundle/name}'
                            for i, name in enumerate(BRIDGES))
        command = ['/usr/bin/qemu-system-x86_64', '-no-user-config', '-nodefaults',
                   '-machine', 'q35', '-accel', 'kvm', '-cpu', 'host', '-m', '2048',
                   '-smp', '2', '-display', 'none', '-nic',
                   ('none' if args.network_none else 'user,restrict=on,ipv6=off,' + forwards), '-monitor', 'none', '-no-reboot',
                   '-drive', f'file={disk},if=virtio,format=qcow2',
                   '-drive', f'file={bundle}/network-seed.iso,media=cdrom,readonly=on',
                   '-serial', f'file:{work}/serial.txt']
        with (work / 'stderr.txt').open('wb') as errors:
            result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=errors, timeout=180)
        if result.returncode:
            raise ValueError('QEMU failed; inspect private diagnostics')
        # The outer service must also bound disk usage: guest serial is untrusted.
        serial = work / 'serial.txt'
        if serial.stat().st_size > 8 * 1024 * 1024:
            raise ValueError('Guest report too large')
        markers = [json.loads(line[17:]) for line in serial.read_text(errors='replace').splitlines()
                   if line.startswith('DAIA_BOOT_RESULT ')]
        if len(markers) != 1 or not isinstance(markers[0], dict) or markers[0].get('nonce') != config['nonce']:
            raise ValueError('Guest correlation result missing')
    finally:
        disk.unlink(missing_ok=True)
    report = {'exit': 0, 'guest': markers[0], 'uid_nonroot': True,
              'private_network': True, 'network_none': args.network_none, 'bundle_verified': True,
              'overlay_removed': not disk.exists(), 'guest_claims_verified': False}
    (work / 'report.json').write_text(json.dumps(report))
    print(json.dumps({'exit': 0, 'bundle_verified': True, 'overlay_removed': report['overlay_removed']}))


if __name__ == '__main__':
    main()

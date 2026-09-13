"""Prepare a credential-free evaluator seed without executing candidate code.

Trusted lab operator inputs only; this does not launch a VM or install services.
The launcher must enforce a fresh isolated VM with no network or credentials.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid


def prepare(candidate, output, iso_builder):
    with Path(candidate).open('rb') as stream:
        raw = stream.read(64 * 1024 + 1)
    if len(raw) > 64 * 1024:
        raise ValueError('Candidate envelope too large')
    source = json.loads(raw)
    if not isinstance(source, str) or len(source.encode()) >= 8192:
        raise ValueError('Bounded source string required')
    output = Path(output)
    output.mkdir()  # Exclusive: never replace existing approved inputs.
    nonce = uuid.uuid4().hex
    template = Path(__file__).with_name('version_evaluator_guest.py').read_text()
    code = template.replace('NONCE', repr(nonce))
    compile(code, 'evaluator-guest', 'exec')  # Syntax only; never execute it.
    cloud = {'users': [], 'package_update': False, 'package_upgrade': False,
             'write_files': [
                 {'path': '/tmp/probe.py', 'content': code, 'permissions': '0444'},
                 {'path': '/tmp/candidate.json', 'content': json.dumps(source),
                  'permissions': '0444'}],
             'runcmd': [['python3', '/tmp/probe.py']],
             'power_state': {'mode': 'poweroff', 'delay': 'now', 'timeout': 30,
                            'condition': True}}
    (output / 'user-data').write_text('#cloud-config\n' + json.dumps(cloud))
    (output / 'meta-data').write_text(json.dumps(
        {'instance-id': 'daia-eval-' + nonce, 'local-hostname': 'daia-eval'}))
    (output / 'network-config').write_text(json.dumps({'version': 2,
        'ethernets': {'unused': {'match': {'name': 'en*'}, 'dhcp4': False,
                                 'dhcp6': False, 'optional': True}}}))
    files = ['user-data', 'meta-data', 'network-config']
    subprocess.run([str(iso_builder), '-quiet', '-output', str(output / 'seed.iso'),
                    '-volid', 'CIDATA', '-joliet', '-rock',
                    *[str(output / name) for name in files]], check=True)
    manifest = {'nonce': nonce,
                'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                'seed_sha256': hashlib.sha256((output / 'seed.iso').read_bytes()).hexdigest(),
                'required_network': 'none', 'provider_credentials': False}
    (output / 'evaluator.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'output', 'iso-builder'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.candidate, args.output, args.iso_builder)))


if __name__ == '__main__':
    main()

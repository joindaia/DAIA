"""Build the public development lab input from repository fixtures.

Operator-approved request template and binaries are supplied explicitly; no login,
model request, package installation or candidate execution occurs in this builder.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid


def prepare(template, native, output, iso_builder, base_sha256):
    if not re.fullmatch('[0-9a-f]{64}', base_sha256):
        raise ValueError('Approved base hash required')
    pins = {'codex': '56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da',
            'bwrap': '52231e1caf55bcbc667b269f49c63599a6f7db4767ae6a039580d0ff853db712'}
    native = Path(native)
    for name, digest in pins.items():
        with (native / name).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                raise ValueError('Native binary pin mismatch')
    with Path(template).open('rb') as stream:
        raw = stream.read(256 * 1024 + 1)
    if len(raw) > 256 * 1024:
        raise ValueError('Request template too large')
    request = json.loads(raw)
    if not isinstance(request, dict):
        raise ValueError('Approved request object required')
    model = request.get('model')
    if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', model):
        raise ValueError('Explicit model identifier required')
    output = Path(output); output.mkdir()
    nonce = uuid.uuid4().hex
    fixture = Path(__file__).parents[1] / 'tests/fixtures/subscription-development'
    code = (fixture / 'probe.py').read_text()
    old = '83344227ed564314a89e1589699e29d9'
    if code.count(old) != 1:
        raise ValueError('Unexpected nonce template')
    code = code.replace(old, nonce)
    if code.count('gpt-5.3-codex-spark') != 1:
        raise ValueError('Unexpected guest model template')
    code = code.replace('gpt-5.3-codex-spark', model)
    compile(code, 'development-guest', 'exec')
    cloud = {'users': [], 'package_update': False, 'package_upgrade': False,
             'write_files': [
                 {'path': '/tmp/probe.py', 'content': code, 'permissions': '0444'},
                 {'path': '/opt/test-template.json', 'content': json.dumps(request), 'permissions': '0444'},
                 {'path': '/work/research.py', 'content': (fixture / 'research.py').read_text(), 'permissions': '0444'}],
             'runcmd': [['python3', '/tmp/probe.py']],
             'power_state': {'mode': 'poweroff', 'delay': 'now', 'timeout': 30, 'condition': True}}
    (output / 'user-data').write_text('#cloud-config\n' + json.dumps(cloud))
    (output / 'meta-data').write_text(json.dumps({'instance-id': 'daia-research-' + nonce, 'local-hostname': 'daia-research'}))
    (output / 'network-config').write_text(json.dumps({'version': 2, 'ethernets': {
        'probe': {'match': {'name': 'en*'}, 'dhcp4': False, 'addresses': ['10.0.2.15/24'],
                  'routes': [{'to': 'default', 'via': '10.0.2.2'}], 'optional': True}}}))
    subprocess.run([str(iso_builder), '-quiet', '-output', str(output / 'seed.iso'),
        '-volid', 'CIDATA', '-joliet', '-rock',
        *[str(output / name) for name in ('user-data', 'meta-data', 'network-config')],
        *[str(native / name) for name in pins]], check=True)
    config = {'nonce': nonce, 'model': model, 'base_sha256': base_sha256,
              'seed_sha256': hashlib.sha256((output / 'seed.iso').read_bytes()).hexdigest()}
    (output / 'config.json').write_text(json.dumps(config))
    # Compatibility input for the current lab controller; never executed by builder.
    (output / 'probe.py').write_bytes(Path(__file__).with_name('run_kvm_lab_guest.py').read_bytes())
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('template', 'native', 'output', 'iso-builder', 'base-sha256'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.template, args.native, args.output, args.iso_builder, args.base_sha256)))


if __name__ == '__main__':
    main()

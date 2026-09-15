"""Derive a direct-worker preboot ISO from an approved native-delivery fixture.

This trusted builder makes no login, model request, VM boot or task execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from prepare_subscription_fixture import COMPANION_PIN
from subscription_lab_task import load_task

NATIVE_PINS = {
    'codex': '56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da',
    'bwrap': '52231e1caf55bcbc667b269f49c63599a6f7db4767ae6a039580d0ff853db712',
}
PROBE_PATH = '/tmp/probe.py'
HELPER_PATH = '/opt/fresh_host_start.py'
MARKER = 'import socket,copy'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def regular(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Pinned regular input required')
    return path


def native_inputs(native, config):
    paths = []
    for name, expected in NATIVE_PINS.items():
        path = regular(Path(native) / name)
        if digest(path) != expected:
            raise ValueError('Native binary pin mismatch')
        paths.append(path)
    companion = Path(native) / 'codex-code-mode-host'
    present = companion.exists() or companion.is_symlink()
    companion_digest = None
    if present:
        companion = regular(companion)
        companion_digest = digest(companion)
        if companion_digest != COMPANION_PIN:
            raise ValueError('Native companion pin mismatch')
        paths.append(companion)
    if (config.get('companion_present') is not present
            or config.get('companion_sha256') != companion_digest):
        raise ValueError('Native companion metadata mismatch')
    return paths


def iso_file(isoinfo, seed, name):
    return subprocess.check_output([str(isoinfo), '-i', str(seed), '-R', '-x', '/' + name],
                                   timeout=10)


def cloud_data(source, isoinfo):
    source = Path(source)
    config = json.loads(regular(source / 'config.json').read_bytes())
    if not (isinstance(config.get('nonce'), str)
            and re.fullmatch('[0-9a-f]{32}', config['nonce'])
            and isinstance(config.get('model'), str)
            and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,127}', config['model'])
            and isinstance(config.get('seed_sha256'), str)
            and re.fullmatch('[0-9a-f]{64}', config['seed_sha256'])):
        raise ValueError('Approved native fixture metadata required')
    seed = regular(source / 'seed.iso')
    if digest(seed) != config['seed_sha256']:
        raise ValueError('Approved native fixture seed mismatch')
    siblings = {name: regular(source / name).read_bytes()
                for name in ('user-data', 'meta-data', 'network-config')}
    for name, data in siblings.items():
        if iso_file(isoinfo, seed, name) != data:
            raise ValueError('Approved seed ' + name + ' mismatch')
    if not siblings['user-data'].startswith(b'#cloud-config\n'):
        raise ValueError('Cloud config header required')
    data = json.loads(siblings['user-data'].split(b'\n', 1)[1])
    if not isinstance(data, dict) or not isinstance(data.get('write_files'), list):
        raise ValueError('Approved cloud write-files required')
    entries = [entry for entry in data['write_files']
               if isinstance(entry, dict) and entry.get('path') == PROBE_PATH]
    if len(entries) != 1 or not isinstance(entries[0].get('content'), str):
        raise ValueError('Unique approved probe required')
    code = entries[0]['content']
    if code.count(MARKER) != 1:
        raise ValueError('Unique pre-network marker required')
    if any(entry.get('path') == HELPER_PATH for entry in data['write_files']
           if isinstance(entry, dict)):
        raise ValueError('Unexpected preboot helper in approved source')
    barrier = ("print('DAIA_PREBOOT native_ready', flush=True)\n"
               "import sys\nsys.path.insert(0, '/opt')\n"
               "from fresh_host_start import ready_and_wait\n"
               "print('DAIA_PREBOOT opening_control', flush=True)\n"
               "with open('/dev/virtio-ports/daia.start', 'r+b', buffering=0) as control:\n"
               " print('DAIA_PREBOOT control_open', flush=True)\n"
               f" ready_and_wait(control, {config['nonce']!r})\n")
    entries[0]['content'] = ("print('DAIA_PREBOOT probe_entered', flush=True)\n"
                             + code.replace(MARKER, barrier + MARKER))
    data['write_files'].append({'path': HELPER_PATH,
                                'content': Path(__file__).with_name('fresh_host_start.py').read_text(),
                                'permissions': '0444'})
    load_task(source, config)
    return config, data, siblings


def prepare(source, native, output, iso_builder, isoinfo):
    config, data, siblings = cloud_data(source, isoinfo)
    inputs = native_inputs(native, config)
    output = Path(output)
    if output.exists():
        raise ValueError('New output directory required')
    output.mkdir(mode=0o700)
    try:
        (output / 'user-data').write_text('#cloud-config\n' + json.dumps(data))
        for name in ('meta-data', 'network-config'):
            (output / name).write_bytes(siblings[name])
        for name in ('probe.py', 'task.json'):
            path = Path(source) / name
            if path.exists():
                shutil.copyfile(regular(path), output / name)
        subprocess.run([str(iso_builder), '-quiet', '-output', str(output / 'seed.iso'),
                        '-volid', 'CIDATA', '-joliet', '-rock',
                        *[str(output / name) for name in ('user-data', 'meta-data', 'network-config')],
                        *[str(path) for path in inputs]], check=True, timeout=30)
        result = dict(config)
        result['seed_sha256'] = digest(output / 'seed.iso')
        (output / 'config.json').write_text(json.dumps(result))
        return result
    except BaseException:
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'native', 'output', 'iso-builder', 'isoinfo'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.native, args.output,
                             args.iso_builder, args.isoinfo)))


if __name__ == '__main__':
    main()

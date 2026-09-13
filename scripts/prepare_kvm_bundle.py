"""Assemble an offline lab bundle from explicitly pinned trusted inputs.

Run on the trusted installation side. This does not authorize input, create a
seed, install services, sign a release or admit a job. Never run task code here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(base, seed, output, *, base_sha256, seed_sha256, nonce):
    if not re.fullmatch('[0-9a-f]{32}', nonce):
        raise ValueError('Exact assignment correlation nonce required')
    inputs = ((Path(base), 'base.qcow2', base_sha256),
              (Path(seed), 'network-seed.iso', seed_sha256))
    for source, _, expected in inputs:
        if (not re.fullmatch('[0-9a-f]{64}', expected) or source.is_symlink()
                or not source.is_file()):
            raise ValueError('Pinned regular input required')
    output = Path(output)
    # Exclusive creation: never overwrite or reuse an existing bundle.
    output.mkdir(mode=0o700)
    try:
        for source, name, expected in inputs:
            target = output / name
            shutil.copyfile(source, target)
            # Hash the copied bytes, not a source that may change during copying.
            if digest(target) != expected:
                raise ValueError('Copied input digest mismatch')
        scripts = Path(__file__).resolve().parent
        shutil.copyfile(scripts / 'run_kvm_lab_guest.py', output / 'launcher.py')
        shutil.copyfile(scripts / 'run_kvm_lab_report.py', output / 'report-wrapper.py')
        bridge = (scripts / 'model_channel_bridge.py').read_text()
        original = '/run/daia-lab/gateway.sock'
        if bridge.count(original) != 1:
            raise ValueError('Unexpected bridge template')
        destinations = {'bridge.py': original,
                        'model-bridge.py': '/run/daia-lab/model.sock',
                        'research-bridge.py': '/run/daia-research/gateway.sock'}
        for name, destination in destinations.items():
            (output / name).write_text(bridge.replace(original, destination))
        config = {'nonce': nonce, 'base_sha256': base_sha256,
                  'seed_sha256': seed_sha256,
                  'bridge_sha256': {name: digest(output / name) for name in destinations}}
        # Written last. The trusted installer must approve all bytes, including
        # the launcher, and protect the output and its ancestors from the worker.
        (output / 'network-config.json').write_text(json.dumps(config, sort_keys=True) + '\n')
        hashes = {p.name: digest(p) for p in sorted(output.iterdir())}
        for path in output.iterdir():
            path.chmod(0o444)
        output.chmod(0o555)
        return hashes
    except BaseException:
        output.chmod(0o700)
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('base', 'seed', 'output', 'base-sha256', 'seed-sha256', 'nonce'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    hashes = prepare(args.base, args.seed, args.output, base_sha256=args.base_sha256,
                     seed_sha256=args.seed_sha256, nonce=args.nonce)
    print(json.dumps({'bundle_files_sha256': hashes}, sort_keys=True))


if __name__ == '__main__':
    main()

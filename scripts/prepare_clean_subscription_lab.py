"""Prepare a fresh Linux lab checkout, runtime and native delivery input.

Trusted installation-side operation only. Does not log in, boot, install host
services or authorize participation. Explicit inputs must already be approved.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def prepare(args):
    if not re.fullmatch(r'[0-9a-f]{40}', args.revision):
        raise ValueError('An exact approved Git commit is required')
    destination = args.output
    if not destination.is_absolute():
        raise ValueError('Use a new absolute output directory')
    # Never reuse a previous runtime, guest or partial installation.
    destination.mkdir(mode=0o700)
    home = destination / 'build-home'
    home.mkdir(mode=0o700)
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
           'HOME': str(home), 'LANG': 'C.UTF-8',
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_TERMINAL_PROMPT': '0',
           'UV_CACHE_DIR': str(args.cache)}
    source = destination / 'source'
    runtime = destination / 'runtime'

    def run(argv, cwd=destination):
        subprocess.run([str(x) for x in argv], cwd=cwd, env=env, check=True)

    run(['git', 'init', '--quiet', source])
    run(['git', '-C', source, 'fetch', '--quiet', '--depth=1', '--',
         args.repository, args.revision])
    actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse',
                                      'FETCH_HEAD'], env=env, text=True).strip()
    if actual != args.revision:
        raise ValueError('Fetched commit differs from approved revision')
    run(['git', '-C', source, 'checkout', '--quiet', '--detach', actual])
    scripts = source / 'scripts'
    run([args.python, scripts / 'verify_lab_base_image.py', '--image', args.image,
         '--checksums', args.checksums, '--signature', args.signature])
    env['UV_PROJECT_ENVIRONMENT'] = str(runtime)
    command = [args.uv, 'sync', '--locked', '--no-editable', '--no-dev',
               '--extra', 'mcp', '--python', args.python]
    if args.offline:
        command.append('--offline')
    run(command, source)
    python = runtime / 'bin/python'
    run([python, '-I', '-m', 'daia.cli', '--help'])
    run([python, scripts / 'prepare_subscription_fixture.py',
         '--template', args.template, '--native', args.native,
         '--output', destination / 'source-fixture', '--iso-builder', args.iso_builder,
         '--base-sha256', '612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354'])
    run([python, scripts / 'prepare_native_delivery_fixture.py',
         '--source', destination / 'source-fixture', '--output', destination / 'guest',
         '--native-directory', args.native, '--iso-builder', args.iso_builder])
    result = {'revision': actual,
              'lock_sha256': hashlib.sha256((source / 'uv.lock').read_bytes()).hexdigest(),
              'guest': json.loads((destination / 'guest/config.json').read_text()),
              'runtime_installed': True, 'guest_prepared': True,
              'provider_called': False, 'guest_booted': False,
              'host_provisioned': False}
    (destination / 'prepared.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    if sys.flags.optimize:
        raise SystemExit('Normal Python execution required')
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repository', 'revision'):
        parser.add_argument('--' + name, required=True)
    for name in ('output', 'cache', 'uv', 'python', 'image', 'checksums',
                 'signature', 'template', 'native', 'iso-builder'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    for name in ('cache', 'uv', 'python', 'image', 'checksums', 'signature',
                 'template', 'native', 'iso_builder'):
        setattr(args, name, getattr(args, name).resolve(strict=(name != 'cache')))
    print(json.dumps(prepare(args)))


if __name__ == '__main__':
    main()

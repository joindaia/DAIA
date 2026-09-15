"""Plan fresh Ubuntu lab tools using trusted, already authenticated APT metadata.

No downloads or installations. An empty package status avoids silently relying
on tools installed on the planning host. Metadata freshness and trust are the
installation administrator's responsibility; SHA-256 alone is not origin proof.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
from urllib.parse import urlsplit

PACKAGES = ('qemu-system-x86', 'qemu-utils', 'genisoimage', 'python3-venv', 'python3-pip')


def parse_plan(text):
    packages = []
    seen = set()
    for line in text.splitlines():
        if not line.startswith("'"):
            continue
        fields = shlex.split(line)
        if len(fields) != 4:
            raise ValueError('Invalid APT package record')
        url, name, size, digest = fields
        parsed = urlsplit(url)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or parsed.username or parsed.password or parsed.fragment
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+%~-]*\.deb', name)
                or name in seen or not size.isdecimal() or int(size) <= 0
                or not re.fullmatch(r'SHA256:[0-9a-fA-F]{64}', digest)):
            raise ValueError('Expected unique package with size and SHA-256')
        seen.add(name)
        packages.append(dict(url=url, filename=name, bytes=int(size), sha256=digest[7:].lower()))
    if not packages:
        raise ValueError('Empty APT plan')
    return packages


def plan(output):
    with tempfile.TemporaryDirectory(prefix='daia-apt-plan-') as folder:
        root = Path(folder)
        status = root / 'status'; status.write_text('')
        archives = root / 'archives'; (archives / 'partial').mkdir(parents=True)
        command = ['apt-get', '-o', 'Acquire::ForceHash=sha256',
                   '-o', 'Dir::State::status=' + str(status),
                   '-o', 'Dir::Cache::archives=' + str(archives),
                   '-o', 'Debug::NoLocking=1', '--print-uris', '--yes',
                   '--download-only', '--no-install-recommends', 'install', *PACKAGES]
        result = subprocess.run(command, capture_output=True, text=True, timeout=45, check=True)
        packages = parse_plan(result.stdout)
    document = {'requested_packages': PACKAGES, 'packages': packages,
                'download_bytes': sum(p['bytes'] for p in packages),
                'downloaded': False, 'installed': False}
    # Exclusive private directory: no overwrite, and no public repository output.
    output = Path(output); output.mkdir(mode=0o700)
    (output / 'packages.json').write_text(json.dumps(document, indent=2) + '\n')
    return {'packages': len(packages), 'download_bytes': document['download_bytes'],
            'downloaded': False, 'installed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(plan(parser.parse_args().output)))

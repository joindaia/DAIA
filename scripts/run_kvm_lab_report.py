"""Trusted service wrapper: export bounded results before private mounts vanish.

Stdout is untrusted JSON for capture in private controller storage, never direct
terminal display or execution. This wrapper adds no VM or credential authority.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def tail(path, limit=4096):
    if not path.is_file():
        return ''
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - limit))
        return stream.read(limit).decode('utf-8', errors='replace')


def failure_context(path):
    """Keep bounded error context even when shutdown chatter follows it."""
    if not path.is_file():
        return ''
    selected = bytearray()
    following = 0
    remaining = 8 * 1024 * 1024
    with path.open('rb') as stream:
        while remaining:
            line = stream.readline(min(8192, remaining))
            if not line:
                break
            remaining -= len(line)
            if any(marker in line for marker in
                   (b'DAIA_NATIVE_FAILURE ', b'Traceback', b'Error:', b'Exception:', b'assert ')):
                following = 4
            if following:
                selected.extend(line[:1024])
                del selected[:-8192]
                following -= 1
    return selected.decode('utf-8', errors='replace')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--network-none', action='store_true')
    args = parser.parse_args()
    bundle = Path(args.bundle)
    failure = 'launcher_failed'
    launcher_error = ''
    try:
        # Anonymous storage in the service's quota-limited /tmp leaves the
        # launcher's required fresh working directory empty.
        with tempfile.TemporaryFile(dir='/tmp') as errors:
            try:
                result = subprocess.run([sys.executable, '-I', str(bundle / 'launcher.py'),
                                         '--bundle', str(bundle)] +
                                        (['--network-none'] if args.network_none else []), timeout=195,
                                        stdout=subprocess.DEVNULL, stderr=errors)
            finally:
                errors.seek(0, 2)
                errors.seek(max(0, errors.tell() - 4096))
                launcher_error = errors.read(4096).decode('utf-8', errors='replace')
        if result.returncode == 0:
            with Path('report.json').open('rb') as stream:
                raw = stream.read(9 * 1024 * 1024 + 1)
            if len(raw) > 9 * 1024 * 1024:
                raise ValueError('Oversized report')
            report = json.loads(raw)
            print(json.dumps({'ok': True, 'report': report}))
            return 0
    except subprocess.TimeoutExpired:
        failure = 'launcher_timeout'
    except (OSError, ValueError):
        failure = 'report_or_launch_error'
    print(json.dumps({'ok': False, 'failure': failure,
                      'untrusted_failure_context': failure_context(Path('serial.txt')),
                      'untrusted_diagnostics': {'launcher-error.txt': launcher_error,
                          **{name: tail(Path(name)) for name in ('stderr.txt', 'serial.txt')}}}))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())

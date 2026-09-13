"""Trusted service wrapper: export bounded results before private mounts vanish.

Stdout is untrusted JSON for capture in private controller storage, never direct
terminal display or execution. This wrapper adds no VM or credential authority.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def tail(path, limit=4096):
    if not path.is_file():
        return ''
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - limit))
        return stream.read(limit).decode('utf-8', errors='replace')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    args = parser.parse_args()
    bundle = Path(args.bundle)
    failure = 'launcher_failed'
    try:
        result = subprocess.run([sys.executable, '-I', str(bundle / 'launcher.py'),
                                 '--bundle', str(bundle)], timeout=195,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
                      'untrusted_diagnostics': {name: tail(Path(name))
                                                for name in ('stderr.txt', 'serial.txt')}}))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())

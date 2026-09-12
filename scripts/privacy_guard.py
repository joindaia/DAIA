"""Small privacy tripwire; NOT a complete secret scanner or anonymity guarantee.

Scans staged blobs and, with --history, every reachable blob and commit metadata.
Never prints detected values. Optional private literals live only in the local
DAIA_PRIVATE_DENYLIST environment variable (newline-separated, never commit it).
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

MAX_BLOB = 2_000_000
EMAIL = re.compile(r"[A-Za-z0-9_.+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
)
PRIVATE_PARTS = {'.private', '.runtime', '.venv', '.codex', '.claude', '__pycache__'}
PRIVATE_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.pem', '.key', '.p12', '.pfx', '.log'}


def email_allowed(value: str) -> bool:
    domain = value.rsplit('@', 1)[1].lower()
    return (domain == 'users.noreply.github.com' or domain.endswith('.example')
            or domain in {'example.com', 'example.org', 'example.net'}
            or value.lower() == 'noreply@github.com')


def scan_text(text: str, private_literals: tuple[str, ...] = ()) -> set[str]:
    found = set()
    if any(not email_allowed(m.group()) for m in EMAIL.finditer(text)):
        found.add('non-placeholder-email')
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        found.add('secret-format')
    if any(literal and literal.casefold() in text.casefold() for literal in private_literals):
        found.add('private-literal')
    return found


def private_path(value: str) -> bool:
    path = Path(value)
    return (bool(set(path.parts) & PRIVATE_PARTS)
            or path.suffix.lower() in PRIVATE_SUFFIXES
            or path.name.endswith(('.contributor.json', '.contributor.lock'))
            or path.name.startswith('.contributor-')
            or (path.name.startswith('.env') and path.name != '.env.example'))


def git(*args: str) -> bytes:
    result = subprocess.run(['git', *args], capture_output=True, check=False)
    if result.returncode:
        # Git diagnostics can contain personal filesystem paths or remote credentials.
        raise RuntimeError('Git inspection failed; run inside a readable repository')
    return result.stdout


def run(history: bool) -> int:
    literals = tuple(x for x in os.environ.get('DAIA_PRIVATE_DENYLIST', '').splitlines() if x)
    problems = []
    blobs: set[str] = set()
    entries = git('ls-files', '--stage', '-z').split(b'\x00')
    for entry in entries:
        if not entry:
            continue
        metadata, raw_name = entry.split(b'\t', 1)
        mode, oid, _stage = metadata.split()
        name = raw_name.decode('utf-8', errors='replace')
        identifier = oid.decode()
        if private_path(name) or scan_text(name, literals):
            problems.append((identifier, 'private-tracked-path'))
        if mode in (b'120000', b'160000'):
            problems.append((identifier, 'symlink-or-submodule-needs-review'))
        else:
            blobs.add(identifier)

    commits: list[str] = []
    if history:
        refs = git('rev-list', '--all').decode().splitlines()
        commits = refs
        for commit in refs:
            text = git('show', '-s', '--format=%an%n%ae%n%cn%n%ce%n%B', commit).decode('utf-8', errors='replace')
            problems.extend((commit, reason) for reason in scan_text(text, literals))
        for line in git('rev-list', '--objects', '--all').decode('utf-8', errors='replace').splitlines():
            oid, _, name = line.partition(' ')
            if name and (private_path(name) or scan_text(name, literals)):
                problems.append((oid, 'private-historical-path'))
            kind = git('cat-file', '-t', oid).strip()
            if kind == b'blob':
                blobs.add(oid)
            elif kind == b'tag':
                text = git('cat-file', '-p', oid).decode('utf-8', errors='replace')
                problems.extend((oid, reason) for reason in scan_text(text, literals))

    for oid in sorted(blobs):
        size = int(git('cat-file', '-s', oid))
        if size > MAX_BLOB:
            problems.append((oid, 'large-blob-needs-manual-review'))
            continue
        raw = git('cat-file', 'blob', oid)
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            problems.append((oid, 'binary-blob-needs-manual-review'))
            continue
        problems.extend((oid, reason) for reason in scan_text(text, literals))
    if problems:
        for oid, category in sorted(set(problems)):
            print(f'REVIEW {oid[:12]} {category}')
        print('Privacy tripwire failed; values were not printed.')
        return 1
    print(f'Privacy tripwire passed: {len(blobs)} blobs, {len(commits)} commits; manual review still required.')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    try:
        return run(args.history)
    except (RuntimeError, OSError, ValueError):
        print('Privacy inspection failed safely; no sensitive diagnostics printed.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

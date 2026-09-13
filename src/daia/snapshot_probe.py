"""Compare coordinator status on a private snapshot without opening the original in SQLite.

Run with the same snapshot and explicit clock on both runtimes. Digests do not
prove source-writer freeze, authenticated MCP access or helper migration.
"""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import sqlite3
from tempfile import TemporaryDirectory

from .crypto import digest
from .service import Coordinator, Denied
from .store import Store, backup_database


def file_digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inspect_snapshot(source, at):
    source = Path(source)
    if type(at) is not int or at < 0:
        raise ValueError('Explicit nonnegative clock required')
    if source.is_symlink() or not source.is_file():
        raise ValueError('Regular private snapshot required')
    if os.name == 'posix' and source.stat().st_mode & 0o077:
        raise ValueError('Private snapshot permissions required')
    if any(Path(str(source) + suffix).exists() for suffix in ('-wal', '-shm', '-journal')):
        raise ValueError('Use a standalone backup snapshot, not a live database')
    before = file_digest(source)
    with TemporaryDirectory(prefix='daia-snapshot-check-') as directory:
        copied = Path(directory) / 'input.sqlite3'
        checked = Path(directory) / 'checked.sqlite3'
        # The temporary directory is private before any database bytes are copied.
        shutil.copyfile(source, copied)
        copied.chmod(0o600)
        if file_digest(copied) != before or file_digest(source) != before:
            raise ValueError('Snapshot changed during inspection')
        backup_database(copied, checked)  # Integrity, foreign keys and audit chain.
        checked_before = file_digest(checked)
        with closing(sqlite3.connect(checked)) as db:
            agents = db.execute('SELECT a.root_id,a.id FROM agents a JOIN contributors c '
                                'ON c.id=a.root_id WHERE a.revoked=0 AND c.revoked=0 '
                                'ORDER BY a.id').fetchall()
        coordinator = Coordinator(Store(str(checked), create=False), clock=lambda: at)
        statuses = []
        for root, agent in agents:
            try:
                status = coordinator.contribution_status(root, agent, migration_check=True, expire=False)
            except Denied as error:
                statuses.append({'denied': str(error)})
            else:
                statuses.append({'status': status})
        if file_digest(checked) != checked_before or file_digest(source) != before:
            raise ValueError('Snapshot changed during inspection')
        return {'at': at, 'snapshot_sha256': before, 'agents_checked': len(agents),
                'status_digest': digest(statuses)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('--at', required=True, type=int)
    args = parser.parse_args()
    try:
        result = inspect_snapshot(args.snapshot, args.at)
    except (OSError, ValueError, sqlite3.Error):
        print('Snapshot inspection refused or failed', file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

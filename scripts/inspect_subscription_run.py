"""Read-only assessment of a retained private subscription lab run.

No credential use, provider connection, retry, signing or automatic resume.
Run only as the trusted operator; output is private operational metadata.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
from subscription_lab_outcome import outcome


def private(path, directory=False):
    if path.is_symlink() or (not path.is_dir() if directory else not path.is_file()):
        raise ValueError('Private regular run paths required')
    if path.stat().st_mode & 0o077:
        raise ValueError('Private run permissions required')


def read_json(path):
    private(path)
    with path.open('rb') as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError('Run record too large')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('Run object required')
    return raw, value


def inspect(run):
    run = Path(run).absolute()
    for directory in (run, run / 'assignment', run / 'coordinator'):
        private(directory, directory=True)
    _, metadata = read_json(run / 'run.json')
    assignment = metadata.get('assignment_id')
    if not isinstance(assignment, str) or not re.fullmatch('[0-9a-f]{32}', assignment):
        raise ValueError('Exact recorded assignment required')
    states = list((run / 'assignment').glob('*.contributor.json'))
    if len(states) != 1:
        raise ValueError('Exactly one saved contributor state required')
    raw, saved = read_json(states[0])
    database = run / 'coordinator/network.sqlite3'; private(database)
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        db.row_factory = sqlite3.Row
        row = db.execute('SELECT id,state,receipt_hash FROM assignments WHERE id=?',
                         (assignment,)).fetchone()
    if read_json(states[0])[0] != raw:
        raise ValueError('State changed during inspection; inspect again after quiescence')
    status = outcome(saved, dict(row) if row else None)
    # A receipt proves delivery, not whether the original client finished its turn.
    status.pop('worker_completed')
    status.update(worker_completion='not_established_by_this_inspection',
                  automatic_resume_authorized=False,
                  model_budget_reconstructed=False)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(inspect(args.run)))


if __name__ == '__main__':
    main()

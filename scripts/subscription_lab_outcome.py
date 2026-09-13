"""Private lab outcome export; no retry, signing, admission or model authority."""
import json
import os
from pathlib import Path
import re
import tempfile


def outcome(saved, assignment):
    result = {'worker_completed': False, 'delivery': 'unconfirmed',
              'automatic_retry_authorized': False}
    if not assignment or assignment.get('state') != 'submitted':
        return result
    expected = assignment.get('receipt_hash')
    if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
        return result
    receipt = saved.get('receipt')
    if (saved.get('pending') is None and saved.get('lease') is None
            and isinstance(receipt, dict) and receipt.get('receipt_hash') == expected):
        result.update(delivery='acknowledged', receipt_hash=expected)
    elif (isinstance(saved.get('pending'), dict)
          and saved['pending'].get('assignment_id') == assignment.get('id')
          and saved.get('pending_receipt_hash') == expected):
        result.update(delivery='stored_unacknowledged', receipt_hash=expected)
    return result


def write_outcome(path, data):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.daia-outcome-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream)
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(parent)
        finally: os.close(parent)
    finally:
        Path(temporary).unlink(missing_ok=True)


def new_run_directory(root):
    """Allocate isolated persistent lab state; never reuse or migrate a run."""
    root = Path(root)
    root.mkdir(mode=0o700, exist_ok=True)
    info = root.lstat()
    if root.is_symlink() or not root.is_dir() or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise ValueError('Private operator-owned state root required')
    run = Path(tempfile.mkdtemp(prefix='run-', dir=root))
    for name in ('assignment', 'coordinator'):
        (run / name).mkdir(mode=0o700)
    for directory in (run, root):
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    return run

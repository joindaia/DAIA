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

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


def retain_model_counts(run, audit):
    """Keep counters and fixed failure categories; never credentials or payload text."""
    result = {'available': False}
    try:
        with Path(audit).open('rb') as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError('Oversized audit')
        data = json.loads(raw)
        counts = {key: data[key] for key in ('forwarded', 'denied', 'attempts')}
        if any(type(value) is not int or value < 0 for value in counts.values()):
            raise ValueError('Invalid counters')
        result = dict(available=True, **counts)
        status = data.get('last_provider_status')
        if type(status) is int and 100 <= status <= 599:
            result['last_provider_status'] = status
        failure = data.get('upstream_failure')
        if type(failure) is str and failure in {
                'upstream binding unavailable', 'upstream response rejected',
                'upstream content type rejected', 'upstream body rejected',
                'upstream encoding rejected', 'upstream framing rejected',
                'upstream response too large', 'upstream length rejected',
                'upstream transport failed'}:
            result['upstream_failure'] = failure
        transport = data.get('transport_failure')
        if (type(transport) is dict and set(transport) == {'phase', 'kind'}
                and transport['phase'] in ('connect', 'send', 'headers', 'body')
                and transport['kind'] in ('timeout', 'http_framing', 'socket')):
            result['transport_failure'] = transport
    except (OSError, ValueError, KeyError, TypeError):
        pass
    write_outcome(Path(run) / 'model-counts.json', result)


def retain_worker_failure(run, process):
    """Private, bounded evidence survives runtime cleanup; never replay it."""
    write_outcome(Path(run) / 'worker-failure-private.json', {
        'returncode': process.returncode,
        'stdout': process.stdout[:64 * 1024].decode('utf-8', errors='replace'),
        'stderr': process.stderr[:64 * 1024].decode('utf-8', errors='replace'),
    })


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

def summarize_outcomes(records):
    totals = {
        'total': 0,
        'worker_completed': 0,
        'acknowledged': 0,
        'stored_unacknowledged': 0,
        'unconfirmed': 0,
    }
    for record in records:
        totals['total'] += 1
        if isinstance(record, dict) and record.get('worker_completed') is True:
            totals['worker_completed'] += 1
        if isinstance(record, dict):
            delivery = record.get('delivery')
            if delivery == 'acknowledged':
                totals['acknowledged'] += 1
            elif delivery == 'stored_unacknowledged':
                totals['stored_unacknowledged'] += 1
            else:
                totals['unconfirmed'] += 1
        else:
            totals['unconfirmed'] += 1
    return totals
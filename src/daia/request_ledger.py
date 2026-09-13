"""Linux trusted-side request accounting across gateway process replacement.

The controller owns creation and the private parent directory. Never expose this
file or its API to workers. A reboot requires a new authorization decision, not
an automatic deadline conversion. This is not an OAuth or token budget ledger.
"""
import fcntl
import json
import math
import os
from pathlib import Path
import re
import stat
import time

from .model_request import Denied


def _boot():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def _now():
    # Includes suspend time; a sleeping host must not extend the assignment.
    return time.clock_gettime(time.CLOCK_BOOTTIME)


def _write(fd, record):
    raw = json.dumps(record, sort_keys=True).encode()
    os.lseek(fd, 0, os.SEEK_SET)
    if os.write(fd, raw) != len(raw):
        raise OSError('Incomplete accounting write')
    os.ftruncate(fd, len(raw))
    os.fsync(fd)  # Must succeed before any provider operation is allowed.


def _open(path, flags):
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077
            or info.st_uid != os.geteuid() or info.st_nlink != 1):
        os.close(fd)
        raise ValueError('Private controller-owned regular accounting file required')
    return fd


def create(path, binding, *, seconds, requests):
    """Explicit trusted authorization: create once; existing state never resets."""
    if (not isinstance(binding, str) or not re.fullmatch('[0-9a-f]{64}', binding)
            or type(seconds) not in (int, float) or not math.isfinite(seconds)
            or not 0 < seconds <= 300 or type(requests) is not int
            or not 0 < requests <= 100):
        raise ValueError('Invalid request authorization')
    fd = _open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL)
    try:
        _write(fd, {'v': 1, 'binding': binding, 'boot': _boot(),
                    'deadline': _now() + seconds, 'remaining': requests})
    finally:
        os.close(fd)
    directory = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _update(path, binding, *, consume):
    fd = None
    try:
        fd = _open(path, os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        raw = os.read(fd, 4097)
        if len(raw) > 4096:
            raise ValueError()
        record = json.loads(raw)
        if (not isinstance(record, dict)
                or set(record) != {'v', 'binding', 'boot', 'deadline', 'remaining'}
                or type(record['v']) is not int or record['v'] != 1
                or not isinstance(binding, str) or not re.fullmatch('[0-9a-f]{64}', binding)
                or record['binding'] != binding
                or type(record['deadline']) not in (int, float)
                or not math.isfinite(record['deadline'])
                or type(record['remaining']) is not int or not 0 <= record['remaining'] <= 100):
            raise ValueError()
        if consume and (record['boot'] != _boot() or _now() >= record['deadline']
                        or record['remaining'] == 0):
            raise ValueError()
        record['remaining'] = record['remaining'] - 1 if consume else 0
        _write(fd, record)
    except (OSError, ValueError, TypeError):
        raise Denied('Persisted request authority unavailable') from None
    finally:
        if fd is not None:
            os.close(fd)


def reserve(path, binding):
    """Consume durably before forwarding; no reset or automatic recovery.

    Private parent ownership and protection against administrator rollback are
    prerequisites. Another boot, expiry, exhaustion or invalid state deny.
    """
    _update(path, binding, consume=True)


def revoke(path, binding):
    """Permanently exhaust this authority, even if already expired/exhausted.

    Idempotent for a valid matching record. Storage/locking failure is reported;
    callers must stop live execution independently and must not claim durability.
    """
    _update(path, binding, consume=False)

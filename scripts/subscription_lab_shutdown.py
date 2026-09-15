"""Read-only post-stop check for the trusted lab supervisor.

Ancestors are operator-protected. No credentials, provider access or resume.
The stop marker is corroboration; matching zero authority is also required.
"""
from contextlib import contextmanager
import json
import os
import re
import stat


@contextmanager
def _directory(path, owner, parent=None):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
    try:
        info = os.fstat(fd)
        if info.st_uid != owner or info.st_mode & 0o077:
            raise ValueError()
        yield fd
    finally:
        os.close(fd)


def _read(directory, name, owner, *, private=True):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != owner or info.st_nlink != 1
                or info.st_mode & (0o077 if private else 0o022)):
            raise ValueError()
        raw = os.read(fd, 4097)
        if len(raw) > 4096:
            raise ValueError()
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError()
        return result
    finally:
        os.close(fd)


def verify(run, *, controller_unit, model_uid):
    """Require this controller's private matching authority and completed revocation.

    A completed delivery, clean socket path or stop marker alone is insufficient.
    Must be called after the trusted supervisor has waited for service termination.
    """
    try:
        if not re.fullmatch(r'daia-controller-job-[a-f0-9]{32}\.service', controller_unit):
            raise ValueError()
        with _directory(run, os.geteuid()) as directory:
            metadata = _read(directory, 'run.json', os.geteuid())
            expected = metadata.get('model_authority_binding')
            if (metadata.get('controller_unit') != controller_unit
                    or not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected)):
                raise ValueError()
            with _directory('model-authority', model_uid, directory) as authority:
                binding = _read(authority, 'binding.json', model_uid)
                ledger = _read(authority, 'requests.json', model_uid)
                marker = _read(authority, 'revoked.json', model_uid, private=False)
        if (binding != {'binding': expected} or ledger.get('binding') != expected
                or type(ledger.get('v')) is not int or ledger['v'] != 1
                or type(ledger.get('remaining')) is not int or ledger['remaining'] != 0
                or set(marker) != {'persisted'} or marker['persisted'] is not True):
            raise ValueError()
    except (OSError, ValueError, TypeError, KeyError):
        raise RuntimeError('Persistent model revocation not established for this controller') from None
    return True

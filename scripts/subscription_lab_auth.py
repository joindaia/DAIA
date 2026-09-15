"""Bounded private-profile reads on the trusted Linux controller only.

The operator must protect all parent directories. This is not a worker API.
"""
import json
import os
from pathlib import Path
import stat


def read_auth(home, *, owner_uid=None, forbidden_uids=()):
    directory = file = None
    try:
        if not Path(home).is_absolute():
            raise ValueError()
        directory = os.open(home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        parent = os.fstat(directory)
        if (parent.st_mode & 0o077 or parent.st_uid in forbidden_uids
                or (owner_uid is not None and parent.st_uid != owner_uid)):
            raise ValueError()
        file = os.open('auth.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        info = os.fstat(file)
        if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077
                or info.st_uid != parent.st_uid or info.st_nlink != 1):
            raise ValueError()
        with os.fdopen(file, 'rb') as stream:
            file = None
            raw = stream.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError()
        data = json.loads(raw)
        tokens = data['tokens']
        if not all(isinstance(tokens[k], str) and tokens[k]
                   for k in ('access_token', 'refresh_token', 'account_id')):
            raise ValueError()
        return data, parent.st_uid
    except (OSError, ValueError, KeyError, TypeError):
        raise RuntimeError('Dedicated private authentication profile rejected') from None
    finally:
        if file is not None: os.close(file)
        if directory is not None: os.close(directory)

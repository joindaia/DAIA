"""Test-only guest /proc inspection; report matches, never captured contents.

The supplied digest identifies a random synthetic 64-hex-character host canary,
not a real credential. Run as guest root. This probes process environments,
arguments and small regular-file handles; it is not a kernel exploit scanner.
"""
import hashlib
import os
from pathlib import Path
import re
import stat

TOKEN = re.compile(rb'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])')
LIMIT = 65536


def contains(raw, digest):
    return any(hashlib.sha256(value).hexdigest() == digest for value in TOKEN.findall(raw))


def inspect(digest):
    if not re.fullmatch('[0-9a-f]{64}', digest):
        raise ValueError('Synthetic canary digest required')
    processes = [p for p in Path('/proc').iterdir() if p.name.isdecimal()]
    if not 0 < len(processes) <= 512:
        raise RuntimeError('Unexpected guest process count')
    result = dict(processes=len(processes), environments=0, arguments=0,
                  regular_handles=0, denied_or_gone=0, matches=0)
    def read(path, kind, regular=False):
        fd = None
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
            if regular:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
                    return
            raw = os.read(fd, LIMIT + 1)
            if len(raw) > LIMIT:
                raise RuntimeError('Process inspection exceeded bound')
            result[kind] += 1
            result['matches'] += int(contains(raw, digest))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            result['denied_or_gone'] += 1
        except OSError as error:
            # Kernel threads and non-file handles can reject reads.
            if error.errno not in (5, 6, 9, 11, 19, 22, 40):
                raise
            result['denied_or_gone'] += 1
        finally:
            if fd is not None:
                os.close(fd)
    for process in processes:
        read(process / 'environ', 'environments')
        read(process / 'cmdline', 'arguments')
        try:
            handles = list((process / 'fd').iterdir())
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            result['denied_or_gone'] += 1
            continue
        if len(handles) > 512:
            raise RuntimeError('Unexpected process handle count')
        for handle in handles:
            # Inspect regular-file handles only; never consume pipes or sockets.
            try:
                if not stat.S_ISREG(handle.stat().st_mode):
                    continue
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
            read(handle, 'regular_handles', regular=True)
    if not result['environments'] or not result['arguments']:
        raise RuntimeError('No process inspection evidence')
    return result

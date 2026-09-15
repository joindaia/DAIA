"""Reject collapsed service identities before the trusted lab reads credentials.

This checks account configuration, not actual service confinement or host safety.
No account is created, modified or granted participation by this check.
"""
import os
import pwd


NAMES = ('daia-controller', 'daia-runtime', 'daia-egress', 'daia-research')


def check_identities():
    try:
        accounts = [pwd.getpwnam(name) for name in NAMES]
        worker_gid = accounts[1].pw_gid
        groups = [os.getgrouplist(a.pw_name, a.pw_gid) for a in accounts]
    except (KeyError, OSError):
        raise RuntimeError('Required lab service identity is unavailable') from None
    if any(a.pw_uid == 0 for a in accounts) or len({a.pw_uid for a in accounts}) != len(NAMES):
        raise RuntimeError('Lab services require distinct nonroot identities')
    if worker_gid == 0 or any(worker_gid in gids for i, gids in enumerate(groups) if i != 1):
        raise RuntimeError('Worker socket group must exclude other lab identities')
    return {'distinct_nonroot_identities': True, 'worker_group_excludes_peers': True}

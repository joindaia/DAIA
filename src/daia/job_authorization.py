"""Verify separately approved work before exposing it to a job-consuming model.

The public key and capability ceiling are operator inputs, never coordinator data.
Lease recovery/submission permission is separate from authorization to execute work.
"""
import json
import os
from pathlib import Path
import stat

from .crypto import digest_bytes, verify, strict_json, validate_public

FIELDS = {'type', 'network_id', 'job_id', 'context_hash', 'policy_hash', 'mode',
          'target_id', 'recipient_agent', 'expires', 'capabilities'}
LEASE_FIELDS = {'assignment_id', 'job_id', 'mode', 'network_id', 'nonce', 'expires',
                'hard_deadline', 'context_hash', 'policy_hash', 'target_id', 'context'}
BOUND_FIELDS = ('network_id', 'job_id', 'context_hash', 'policy_hash', 'mode', 'target_id')


def verify_job(lease, authorization, *, public_key, agent_id, network_id,
               allowed_capabilities, now):
    """Return authorized capabilities or fail with a content-free error."""
    try:
        # Reject unsigned extra instruction fields rather than forwarding them.
        if not isinstance(lease, dict) or set(lease) != LEASE_FIELDS:
            raise ValueError()
        if not isinstance(authorization, dict) or set(authorization) != {'payload', 'signature'}:
            raise ValueError()
        # These lease identifiers may change on reassignment, but cannot carry
        # arbitrary coordinator text outside the signed job context.
        for field, size in (('assignment_id', 32), ('nonce', 64)):
            value = lease[field]
            if (not isinstance(value, str) or len(value) != size
                    or any(char not in '0123456789abcdef' for char in value)):
                raise ValueError()
        payload = authorization['payload']
        if (not isinstance(payload, dict) or set(payload) != FIELDS
                or payload['type'] != 'daia-job-authorization-v1'
                or not verify(public_key, payload, authorization['signature'])
                or payload['recipient_agent'] != agent_id
                or payload['network_id'] != network_id
                or any(payload[field] != lease[field] for field in BOUND_FIELDS)):
            raise ValueError()
        expiry = payload['expires']
        if (type(now) is not int or type(expiry) is not int or now >= expiry
                or type(lease['expires']) is not int
                or type(lease['hard_deadline']) is not int
                or not now < lease['expires'] <= lease['hard_deadline'] <= expiry):
            raise ValueError()
        capabilities = payload['capabilities']
        if (not isinstance(capabilities, list)
                or any(not isinstance(item, str) for item in capabilities)
                or len(set(capabilities)) != len(capabilities)
                or not set(capabilities) <= set(allowed_capabilities)):
            raise ValueError()
        context = json.dumps(lease['context'], ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False).encode('utf-8')
        if digest_bytes(context) != payload['context_hash']:
            raise ValueError()
        return tuple(capabilities)
    except (KeyError, TypeError, ValueError, RecursionError, OverflowError):
        raise ValueError('Job authorization refused') from None


def load_job_authority(path):
    """Read a bounded operator policy; never obtain this file from a job."""
    try:
        path = Path(path).absolute()
        if path.resolve() != path:
            raise ValueError()
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        with os.fdopen(os.open(path, flags), 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode)
                    or (os.name == 'posix' and (info.st_uid not in {0, os.geteuid()}
                                               or info.st_mode & 0o022))):
                raise ValueError()
            raw = stream.read(262145)
        if len(raw) > 262144:
            raise ValueError()
        policy = strict_json(raw.decode('utf-8'))
        if not isinstance(policy, dict) or set(policy) != {'public_key', 'capabilities', 'jobs'}:
            raise ValueError()
        validate_public(policy['public_key'])
        caps = policy['capabilities']
        if (not isinstance(caps, list) or any(not isinstance(v, str) or not v for v in caps)
                or len(caps) != len(set(caps)) or not isinstance(policy['jobs'], dict)):
            raise ValueError()
        return policy
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        raise ValueError('Local job authorization policy refused') from None


def authorize_job(lease, *, key, agent_id, capabilities, expires, now):
    """Sign an operator-reviewed package; this function does not review its content."""
    from .crypto import sign, public_hex
    try:
        payload = {field: lease[field] for field in BOUND_FIELDS}
        payload.update(type='daia-job-authorization-v1', recipient_agent=agent_id,
                       capabilities=list(capabilities), expires=expires)
        authorization = {'payload': payload, 'signature': sign(key, payload)}
        verify_job(lease, authorization, public_key=public_hex(key), agent_id=agent_id,
                   network_id=lease['network_id'], allowed_capabilities=capabilities, now=now)
        return authorization
    except (KeyError, ValueError, TypeError):
        raise ValueError('Reviewed job could not be authorized') from None


def main():
    import argparse
    import time
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    parser = argparse.ArgumentParser(description='Sign an explicitly reviewed job locally; no network or consent changes')
    parser.add_argument('--reviewed-job', type=Path, required=True)
    parser.add_argument('--key', type=Path, required=True, help='Private raw 32-byte Ed25519 key')
    parser.add_argument('--agent', required=True)
    parser.add_argument('--capability', action='append', required=True)
    parser.add_argument('--expires', type=int, required=True, help='Absolute Unix authorization expiry')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
        if args.key.absolute().resolve() != args.key.absolute():
            raise ValueError()
        with os.fdopen(os.open(args.key, flags), 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or (os.name == 'posix' and
                    (info.st_uid not in {0, os.geteuid()} or info.st_mode & 0o077))):
                raise ValueError()
            key = Ed25519PrivateKey.from_private_bytes(stream.read(33))
        if args.reviewed_job.absolute().resolve() != args.reviewed_job.absolute():
            raise ValueError()
        with os.fdopen(os.open(args.reviewed_job, flags), 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or (os.name == 'posix' and
                    (info.st_uid not in {0, os.geteuid()} or info.st_mode & 0o022))):
                raise ValueError()
            raw = stream.read(262145)
        if len(raw) > 262144:
            raise ValueError()
        lease = strict_json(raw.decode('utf-8'))
        authorization = authorize_job(lease, key=key, agent_id=args.agent,
                                       capabilities=args.capability, expires=args.expires,
                                       now=int(time.time()))
        descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(authorization, stream, sort_keys=True)
            stream.write('\n')
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        parser.exit(1, 'Job signing refused; check reviewed input, private key, bounds and unused output path\n')
    print('Reviewed job authorization written; no participant consent changed.')


if __name__ == '__main__':
    main()

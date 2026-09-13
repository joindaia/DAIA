"""Trusted lab authorization preparation; never called by a worker.

Creates a new per-run ledger before model service startup. No recovery, refresh,
provider access or secret storage. The launcher binds this private directory into
only the model service and assigns its ownership to that service identity.
"""
import hashlib
import json
from pathlib import Path
from daia.request_ledger import create
from subscription_lab_outcome import write_outcome


def prepare(run, *, lease, consent_deadline, template, account, deadline):
    if not isinstance(lease, dict) or not lease.get('assignment_id'):
        raise ValueError('Recorded assignment required')
    if not isinstance(account, str) or not account or not isinstance(template, bytes):
        raise ValueError('Trusted account and template required')
    scope = {'lease': lease, 'consent_deadline': consent_deadline,
             'template_sha256': hashlib.sha256(template).hexdigest(),
             'account': account, 'provider': 'codex', 'requests': 6,
             'deadline_boottime': deadline}
    binding = hashlib.sha256(json.dumps(scope, sort_keys=True, separators=(',', ':'),
                                      allow_nan=False).encode()).hexdigest()
    directory = Path(run) / 'model-authority'
    directory.mkdir(mode=0o700)  # Never reopen or reset a preceding authority.
    create(directory / 'requests.json', binding, seconds=150, requests=6, deadline=deadline)
    write_outcome(directory / 'binding.json', {'binding': binding})
    return binding

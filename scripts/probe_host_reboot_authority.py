"""Two-phase credential-free host reboot check. Does not restart the host.

Run prepare and verify as the same trusted test administrator, with an actual
host reboot between them. No credential, model, assignment or automatic resume.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from daia.model_request import Denied
from daia.request_ledger import create, reserve
from subscription_lab_outcome import write_outcome

BINDING = 'a' * 64
BOOT_ID_PATH = Path('/proc/sys/kernel/random/boot_id')
RUN_ROOT = Path('/run')


def probe(phase, root):
    root = Path(root)
    if not root.is_absolute() or root.is_symlink():
        raise ValueError('Private absolute persistent directory required')
    ledger = root / 'requests.json'
    boot = BOOT_ID_PATH.read_text().strip()
    marker = RUN_ROOT / ('daia-reboot-' + hashlib.sha256(str(root).encode()).hexdigest()[:20])
    if phase == 'prepare':
        root.mkdir(mode=0o700)
        create(ledger, BINDING, seconds=300, requests=2)
        reserve(ledger, BINDING)
        marker.write_text('synthetic reboot marker')
        marker.chmod(0o600)
        write_outcome(root / 'before.json', {'boot': boot,
                      'ledger_sha256': hashlib.sha256(ledger.read_bytes()).hexdigest()})
        return {'prepared': True, 'reservation_before_reboot': True,
                'provider_requests': 0, 'credentials_used': False}
    if phase != 'verify':
        raise ValueError('Unknown phase')
    before = json.loads((root / 'before.json').read_text())
    if before['boot'] == boot:
        raise RuntimeError('No actual host reboot observed')
    raw = ledger.read_bytes()
    if hashlib.sha256(raw).hexdigest() != before['ledger_sha256']:
        raise RuntimeError('Persistent ledger changed before verification')
    record = json.loads(raw)
    if record['remaining'] != 1 or time.clock_gettime(time.CLOCK_BOOTTIME) >= record['deadline']:
        raise RuntimeError('Cannot distinguish boot refusal from budget/expiry refusal')
    try:
        reserve(ledger, BINDING)
    except Denied:
        pass
    else:
        raise RuntimeError('Pre-reboot authority was reused')
    if ledger.read_bytes() != raw or marker.exists():
        raise RuntimeError('Old authority mutated or volatile marker survived')
    result = {'host_boot_changed': True, 'old_authority_denied': True,
              'unexpired_nonempty_ledger_unchanged': True,
              'volatile_marker_removed': True, 'credentials_used': False,
              'provider_requests': 0, 'automatic_resume': False}
    write_outcome(root / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'verify'])
    parser.add_argument('--state', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(probe(args.phase, args.state)))

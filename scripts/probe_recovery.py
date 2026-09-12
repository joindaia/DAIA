"""Disposable process-restart recovery probe; never opens a real coordinator DB."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from daia.crypto import public_hex, sign
from daia.service import Coordinator, Denied
from daia.store import Store, backup_database


def resume(folder):
    folder = Path(folder)
    pending = json.loads((folder / 'pending.json').read_text())
    assert not (folder / 'source.sqlite3').exists()
    service = Coordinator(Store(str(folder / 'restored.sqlite3'), create=False),
                          clock=lambda: pending['clock'])
    assert service.network_id == pending['network_id']
    args = pending['submission']
    before = service.contribution_status(args[0], args[1])
    assert before == pending['contribution_status']
    assert before['assigned'] == before['max_jobs'] == 1
    receipt = service.submit(*args)
    assert receipt == {'receipt_hash': pending['receipt_hash'], 'status': 'already_recorded'}
    assert service.submit(*args) == receipt
    assert service.metrics()['results'] == 1
    assert service.contribution_status(args[0], args[1]) == before
    altered = args.copy()
    altered[3] = '{"factors":[1,10403]}'
    try:
        service.submit(*altered)
    except Denied:
        pass
    else:
        raise AssertionError('Altered submission accepted')
    assert service.metrics()['results'] == 1
    print('restored receipt replay preserved identity, grant and single result')


def main():
    if not __debug__:
        raise SystemExit("Recovery probe requires assertions; disable Python optimization")
    if len(sys.argv) == 3 and sys.argv[1] == '--resume':
        resume(sys.argv[2])
        return
    if len(sys.argv) != 1:
        raise SystemExit('No arguments, or internal --resume DIRECTORY expected')
    with TemporaryDirectory(prefix='daia-recovery-probe-') as temporary:
        folder = Path(temporary)
        clock = 1800000000
        service = Coordinator(Store(str(folder / 'source.sqlite3')), clock=lambda: clock)
        service.seed()
        grant = service.invite(max_jobs=1)
        key = Ed25519PrivateKey.generate()
        challenge = service.challenge(grant['root_id'], public_hex(key))
        agent = service.register(grant['root_id'], challenge['challenge_id'], sign(key, challenge))['agent_id']
        lease = service.request_work(grant['root_id'], agent)
        args = [grant['root_id'], agent, lease['assignment_id'], '{"factors":[101,103]}', 'candidate']
        args.append(sign(key, service.envelope(*args)))
        receipt = service.submit(*args)
        assert receipt['status'] == 'in_review'
        pending = {'submission': args, 'clock': clock, 'network_id': service.network_id,
                   'receipt_hash': receipt['receipt_hash'],
                   'contribution_status': service.contribution_status(grant['root_id'], agent)}
        (folder / 'pending.json').write_text(json.dumps(pending))
        backup_database(folder / 'source.sqlite3', folder / 'restored.sqlite3')
        # No process serving the source remains, and the child cannot reopen it.
        (folder / 'source.sqlite3').unlink()
        subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--resume', temporary],
                       stdin=subprocess.DEVNULL, check=True, timeout=15)


if __name__ == '__main__':
    main()

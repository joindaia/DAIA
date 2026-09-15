import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from daia import request_ledger as ledger


SCRIPTS = Path(__file__).parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location(
    'probe_host_reboot_authority', SCRIPTS / 'probe_host_reboot_authority.py')
reboot_probe = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(SCRIPTS))
try:
    spec.loader.exec_module(reboot_probe)
finally:
    sys.path.pop(0)


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    boot_id = tmp_path / 'boot-id'
    boot_id.write_text('boot-before\n')
    run_root = tmp_path / 'run'
    run_root.mkdir()
    now = [100.0]
    monkeypatch.setattr(reboot_probe, 'BOOT_ID_PATH', boot_id)
    monkeypatch.setattr(reboot_probe, 'RUN_ROOT', run_root)
    monkeypatch.setattr(ledger, '_boot', lambda: boot_id.read_text().strip())
    monkeypatch.setattr(ledger, '_now', lambda: now[0])
    monkeypatch.setattr(reboot_probe.time, 'clock_gettime', lambda _: now[0])
    root = tmp_path / 'persistent-state'
    reboot_probe.probe('prepare', root)
    return root, boot_id, run_root, now


def marker(root, run_root):
    name = 'daia-reboot-' + hashlib.sha256(str(root).encode()).hexdigest()[:20]
    return run_root / name


def after_reboot(root, boot_id, run_root):
    boot_id.write_text('boot-after\n')
    marker(root, run_root).unlink()


def test_verify_accepts_changed_boot_and_preserved_unexpired_ledger(prepared):
    root, boot_id, run_root, _ = prepared
    ledger_path = root / 'requests.json'
    before = json.loads((root / 'before.json').read_text())
    raw = ledger_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == before['ledger_sha256']
    record = json.loads(raw)
    assert record['remaining'] == 1 and record['deadline'] > 100
    after_reboot(root, boot_id, run_root)

    result = reboot_probe.probe('verify', root)

    assert result['host_boot_changed'] is True
    assert result['old_authority_denied'] is True
    assert result['unexpired_nonempty_ledger_unchanged'] is True
    assert ledger_path.read_bytes() == raw


def test_verify_rejects_unchanged_boot(prepared):
    root, _, _, _ = prepared
    raw = (root / 'requests.json').read_bytes()

    with pytest.raises(RuntimeError, match='No actual host reboot observed'):
        reboot_probe.probe('verify', root)

    assert (root / 'requests.json').read_bytes() == raw


def test_verify_rejects_persistent_ledger_mutation(prepared):
    root, boot_id, run_root, _ = prepared
    ledger_path = root / 'requests.json'
    ledger_path.write_bytes(ledger_path.read_bytes() + b' ')
    after_reboot(root, boot_id, run_root)

    with pytest.raises(RuntimeError, match='Persistent ledger changed'):
        reboot_probe.probe('verify', root)


def test_verify_rejects_expired_ledger_before_boot_refusal(prepared):
    root, boot_id, run_root, now = prepared
    record = json.loads((root / 'requests.json').read_text())
    now[0] = record['deadline']
    after_reboot(root, boot_id, run_root)

    with pytest.raises(RuntimeError, match='Cannot distinguish'):
        reboot_probe.probe('verify', root)


def test_verify_rejects_depleted_original_ledger(prepared):
    root, boot_id, run_root, _ = prepared
    ledger_path = root / 'requests.json'
    record = json.loads(ledger_path.read_text())
    record['remaining'] = 0
    raw = json.dumps(record, sort_keys=True).encode()
    ledger_path.write_bytes(raw)
    before_path = root / 'before.json'
    before = json.loads(before_path.read_text())
    before['ledger_sha256'] = hashlib.sha256(raw).hexdigest()
    before_path.write_text(json.dumps(before))
    after_reboot(root, boot_id, run_root)

    with pytest.raises(RuntimeError, match='Cannot distinguish'):
        reboot_probe.probe('verify', root)

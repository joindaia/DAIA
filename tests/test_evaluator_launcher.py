"""Networkless launch selection and external service cleanup constraints."""
import json
from pathlib import Path
import runpy
import types
import pytest

ROOT = Path(__file__).parents[1]


def test_networkless_launcher_has_no_guest_forwarders(tmp_path, monkeypatch):
    scope = runpy.run_path(str(ROOT / 'scripts/run_kvm_lab_guest.py'))
    main = scope['main']; g = main.__globals__
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr('sys.argv', ['launcher', '--bundle', '/approved/bundle', '--network-none'])
    monkeypatch.setattr('os.getuid', lambda: 1234)
    monkeypatch.setattr('socket.if_nameindex', lambda: [(1, 'lo')])
    monkeypatch.setattr(Path, 'is_char_device', lambda self: str(self) == '/dev/kvm')
    g['verify_bundle'] = lambda _: {'nonce': 'a' * 32}
    commands = []
    def run(argv, **kwargs):
        commands.append(argv)
        if argv[0].endswith('qemu-img'):
            (tmp_path / 'guest.qcow2').write_bytes(b'synthetic disk')
        else:
            assert argv[argv.index('-nic') + 1] == 'none'
            assert not any('guestfwd=' in arg for arg in argv)
            (tmp_path / 'serial.txt').write_text('DAIA_BOOT_RESULT ' + json.dumps({'nonce': 'a'*32}))
        return types.SimpleNamespace(returncode=0)
    monkeypatch.setattr('subprocess.run', run)
    main()
    assert len(commands) == 2 and not (tmp_path / 'guest.qcow2').exists()
    assert json.loads((tmp_path / 'report.json').read_text())['network_none'] is True


def test_service_storage_is_external_and_bounded():
    scope = runpy.run_path(str(ROOT / 'scripts/run_evaluator_lab.py'))
    p = scope['properties'](Path('/approved/work'), types.SimpleNamespace(pw_uid=123,pw_gid=456))
    assert p['KillMode'] == 'control-group' and p['Restart'] == 'no'
    assert p['PrivateNetwork'] == 'yes' and p['CapabilityBoundingSet'] == ''
    assert p['MemorySwapMax'] == '0' and p['RuntimeMaxSec'] == '210'
    assert '/approved/work:size=512M,nr_inodes=4096' in p['TemporaryFileSystem']
    assert 'ReadWritePaths' not in p

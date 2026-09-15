"""Direct host result transport rejects replay and malformed export."""
import importlib.util
import json
from pathlib import Path
import socket
import sys
import time

import pytest

if sys.platform != 'linux':
    pytest.skip('Linux/KVM host acceptance tests', allow_module_level=True)

scripts = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(scripts))
try:
    spec = importlib.util.spec_from_file_location('fresh_host_controller', scripts / 'fresh_host_controller.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
finally:
    sys.path.pop(0)


@pytest.mark.parametrize('payload,accepted', [
    (b'{"ok":true,"report":{}}', True), (b'{"ok":false}', True),
    (b'{"ok":1}', False), (b'[]', False),
])
def test_result_transport_and_one_start(tmp_path, payload, accepted):
    host, guest = socket.socketpair()
    obj = module.PreparedHost.__new__(module.PreparedHost)
    obj.connection, obj.nonce, obj.started = host, 'a'*32, False
    obj.result = tmp_path / 'result.json'
    obj.result.write_bytes(payload)
    closed = []
    obj.close = lambda: closed.append(True)
    with host, guest:
        if accepted:
            result = obj.run(time.monotonic() + 2)
            assert closed == [True]
            assert result.stdout == payload
            assert result.returncode == (0 if json.loads(payload)['ok'] else 1)
        else:
            with pytest.raises(ValueError): obj.run(time.monotonic() + 2)
        assert closed == [True]
        assert obj.connection is None
        assert guest.recv(100) == b'DAIA_START '+b'a'*32+b'\n'
        with pytest.raises(ValueError, match='already started'):
            obj.run(time.monotonic() + 2)


def test_oversized_export_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'MAX_REPORT', 32)
    path = tmp_path / 'result.json'; path.write_bytes(b' '*33)
    with pytest.raises(ValueError, match='Oversized'):
        module.result_bytes(path)


def test_missing_result_stops_at_assignment_deadline(tmp_path):
    host, guest = socket.socketpair()
    obj = module.PreparedHost.__new__(module.PreparedHost)
    obj.connection, obj.nonce, obj.started = host, 'a'*32, False
    obj.result = tmp_path / 'missing.json'
    events = []
    obj.close = lambda: events.append('closed')
    obj.retain_boot_failure = lambda: events.append('diagnostic')
    with host, guest:
        with pytest.raises(TimeoutError, match='result timeout'):
            obj.run(time.monotonic() + .01)
        assert events == ['diagnostic', 'closed']
        assert obj.connection is None
        assert guest.recv(100).startswith(b'DAIA_START ')
        assert guest.recv(1) == b''

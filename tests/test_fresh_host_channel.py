"""Fixed destinations and real duplex transfer without provider credentials."""
import importlib.util
from pathlib import Path
import socket
import sys
import threading

import pytest

pytestmark = pytest.mark.skipif(sys.platform != 'linux', reason='Linux socket relay')


@pytest.fixture
def channel(monkeypatch):
    scripts = Path(__file__).parents[1] / 'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location('fresh_host_channel', scripts / 'fresh_host_channel.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('name,address', [('assignment', '10.0.2.100'),
                                         ('model', '10.0.2.101'),
                                         ('research', '10.0.2.102')])
def test_fixed_destination_and_real_duplex(channel, monkeypatch, name, address):
    client, worker = socket.socketpair()
    upstream, host = socket.socketpair()
    errors = []
    def connect(destination, timeout):
        assert destination == (address, 3128)
        assert timeout == 5
        return upstream
    monkeypatch.setattr(channel.socket, 'create_connection', connect)
    def run():
        try: channel.forward(client, name)
        except Exception as error: errors.append(error)
    thread = threading.Thread(target=run)
    try:
        host.settimeout(2); worker.settimeout(2); thread.start()
        worker.sendall(b'bounded request')
        assert host.recv(100) == b'bounded request'
        host.sendall(b'bounded response'); host.shutdown(socket.SHUT_WR)
        assert worker.recv(100) == b'bounded response'
        thread.join(2)
        assert not thread.is_alive() and not errors
    finally:
        worker.close(); client.close(); host.close(); upstream.close()
        thread.join(2)


def test_no_user_selected_destination(channel):
    with pytest.raises(KeyError): channel.forward(None, 'https://example.invalid')


def test_connection_time_consumes_transport_budget(channel, monkeypatch):
    ticks = iter([100, 251])
    monkeypatch.setattr(channel.time, 'monotonic', lambda: next(ticks))
    upstream, host = socket.socketpair()
    monkeypatch.setattr(channel.socket, 'create_connection', lambda *a, **k: upstream)
    try:
        with pytest.raises(TimeoutError): channel.forward(None, 'assignment')
    finally: host.close()


@pytest.mark.parametrize('mode', [0o777, 0o770])
def test_public_or_group_writable_parent_refused(channel, tmp_path, monkeypatch, mode):
    parent = tmp_path / 'endpoint'; parent.mkdir(mode=mode); parent.chmod(mode)
    endpoint = parent / 'model.sock'
    monkeypatch.setitem(channel.CHANNELS, 'model', (str(endpoint), '10.0.2.101', 30, 100))
    with pytest.raises(ValueError): channel.serve('model')
    assert not endpoint.exists()

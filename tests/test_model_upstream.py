import http.server
import socketserver
import threading
import time

import pytest
from daia.model_request import Denied
from daia.model_upstream import LocalModelUpstream

pytestmark = pytest.mark.skipif(not hasattr(socketserver, 'UnixStreamServer'), reason='Unix lab transport')


@pytest.fixture
def upstream(tmp_path):
    state = {'status': 200, 'body': b'data: {}\n\n', 'seen': [], 'started': threading.Event(), 'release': threading.Event(), 'wait': False}
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            state['seen'].append((self.path, self.headers['Authorization'], body))
            state['started'].set()
            if state['wait']: state['release'].wait(3)
            try:
                self.send_response(state['status'])
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Content-Length', str(len(state['body'])))
                self.end_headers()
                if state.get('drip'):
                    for byte in state['body']:
                        self.wfile.write(bytes([byte])); self.wfile.flush()
                        time.sleep(.05)
                else:
                    self.wfile.write(state['body'])
            except BrokenPipeError: pass
    path = str(tmp_path / 'provider.sock')
    with socketserver.UnixStreamServer(path, Handler) as server:
        t = threading.Thread(target=server.serve_forever); t.start()
        try: yield path, state
        finally: state['release'].set(); server.shutdown(); t.join(5)


def test_inject_fixed_credential_and_exhaust_budget(upstream):
    path, state = upstream
    binding = LocalModelUpstream(path, 'synthetic-secret', seconds=5, requests=1)
    assert binding(b'{}') == state['body']
    assert state['seen'] == [('/v1/responses', 'Bearer synthetic-secret', b'{}')]
    with pytest.raises(Denied): binding(b'{}')
    assert len(state['seen']) == 1


@pytest.mark.parametrize('status,body', [(302, b'redirect'), (401, b'error'), (200, b'synthetic-secret')])
def test_response_failures_do_not_escape(upstream, status, body):
    path, state = upstream; state.update(status=status, body=body)
    with pytest.raises(Denied) as error:
        LocalModelUpstream(path, 'synthetic-secret', seconds=5, requests=1)(b'{}')
    assert 'synthetic-secret' not in str(error.value)


def test_revocation_interrupts_inflight_response(upstream):
    path, state = upstream; state['wait'] = True
    binding = LocalModelUpstream(path, 'synthetic-secret', seconds=5, requests=2)
    errors = []
    def call():
        try: binding(b'{}')
        except Denied: errors.append(True)
    t = threading.Thread(target=call); t.start()
    assert state['started'].wait(2)
    binding.revoke(); t.join(2)
    assert not t.is_alive() and errors == [True]
    with pytest.raises(Denied): binding(b'{}')
    assert len(state['seen']) == 1


def test_expired_binding_does_not_connect(upstream):
    path, state = upstream
    binding = LocalModelUpstream(path, 'synthetic-secret', seconds=.001, requests=1)
    time.sleep(.01)
    with pytest.raises(Denied): binding(b'{}')
    assert state['seen'] == []


@pytest.mark.parametrize('secret', ['', None, 'a\r\nX-Evil: yes', 'with space', 'x' * 8193])
def test_invalid_credential_rejected_before_connect(secret):
    with pytest.raises(ValueError):
        LocalModelUpstream('/nonexistent', secret, seconds=5, requests=1)


def test_jwt_shaped_credential_is_injected_exactly(upstream):
    path, state = upstream
    secret = 'synthetic.header.signature'
    binding = LocalModelUpstream(path, secret, seconds=5, requests=1)
    assert binding(b'{}') == state['body']
    assert state['seen'] == [('/v1/responses', 'Bearer ' + secret, b'{}')]


def test_rotation_preserves_budget_and_injects_new_credential(upstream):
    path, state = upstream
    binding = LocalModelUpstream(path, 'before', seconds=5, requests=2)
    binding(b'{}')
    binding.replace_credential('after')
    binding(b'{}')
    with pytest.raises(Denied): binding.replace_credential('another')
    with pytest.raises(Denied): binding(b'{}')
    assert [entry[1] for entry in state['seen']] == ['Bearer before', 'Bearer after']


def test_rotation_cannot_extend_deadline(upstream, monkeypatch):
    path, state = upstream
    now = [100.0]
    monkeypatch.setattr('daia.model_upstream.time.monotonic', lambda: now[0])
    binding = LocalModelUpstream(path, 'before', seconds=5, requests=2)
    now[0] = 104.0
    binding.replace_credential('after')
    now[0] = 105.0
    with pytest.raises(Denied): binding.replace_credential('another')
    with pytest.raises(Denied): binding(b'{}')
    assert state['seen'] == []


def test_rotation_cannot_revive_revoked_binding(upstream):
    path, state = upstream
    binding = LocalModelUpstream(path, 'before', seconds=5, requests=2)
    binding.revoke()
    with pytest.raises(Denied): binding.replace_credential('after')
    with pytest.raises(Denied): binding(b'{}')
    assert state['seen'] == []


def test_rotation_during_request_is_rejected(upstream):
    path, state = upstream
    state['wait'] = True
    binding = LocalModelUpstream(path, 'before', seconds=5, requests=2)
    outputs = []
    thread = threading.Thread(target=lambda: outputs.append(binding(b'{}')))
    thread.start()
    try:
        assert state['started'].wait(2)
        with pytest.raises(Denied): binding.replace_credential('after')
    finally:
        state['release'].set(); thread.join(5)
    assert not thread.is_alive() and outputs == [state['body']]
    binding.replace_credential('after')
    binding(b'{}')
    assert [entry[1] for entry in state['seen']] == ['Bearer before', 'Bearer after']


def test_invalid_rotation_does_not_replace_current_credential(upstream):
    path, state = upstream
    binding = LocalModelUpstream(path, 'before', seconds=5, requests=1)
    with pytest.raises(ValueError): binding.replace_credential('bad\r\nHeader: value')
    binding(b'{}')
    assert state['seen'][0][1] == 'Bearer before'


def test_deadline_interrupts_continuously_arriving_body(upstream):
    path, state = upstream
    state.update(drip=True, body=b'x' * 100)
    binding = LocalModelUpstream(path, 'synthetic-secret', seconds=.3, requests=2)
    errors = []
    def call():
        try: binding(b'{}')
        except Denied: errors.append(True)
    thread = threading.Thread(target=call)
    thread.start()
    try:
        assert state['started'].wait(2)
        thread.join(1)
        assert not thread.is_alive(), 'active response outlived assignment deadline'
        assert errors == [True]
        with pytest.raises(Denied): binding(b'{}')
        assert len(state['seen']) == 1
    finally:
        binding.revoke()
        thread.join(2)

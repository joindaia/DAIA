import datetime
import http.server
import socket
import ssl
import threading
import time

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from daia.codex_https import CodexHTTPSUpstream
from daia.model_request import Denied


@pytest.fixture
def provider(tmp_path, monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'chatgpt.com')])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=1))
            .not_valid_after(now + datetime.timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName('chatgpt.com')]), critical=False)
            .sign(key, hashes.SHA256()))
    certfile = tmp_path / 'cert.pem'; certfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    keyfile = tmp_path / 'key.pem'; keyfile.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    keyfile.chmod(0o600)
    state = {'status': 200, 'seen': [], 'connections': [], 'started': threading.Event()}
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            state['seen'].append((self.path, dict(self.headers), body))
            state['started'].set()
            self.send_response(state['status'])
            for value in state.get('content_types', ['text/event-stream']):
                self.send_header('Content-Type', value)
            for name, value in state.get('framing', [('Content-Length', '10')]):
                self.send_header(name, value)
            self.send_header('Location', 'https://example.invalid/account')
            self.end_headers()
            try:
                if state.get('drip'):
                    for _ in range(100):
                        self.wfile.write(b'1\r\nx\r\n'); self.wfile.flush()
                        time.sleep(.05)
                else:
                    self.wfile.write(state.get('wire', b'data: {}\n\n'))
            except (BrokenPipeError, ConnectionResetError, ssl.SSLError):
                pass
    with http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile, keyfile)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        original = socket.socket.connect
        def local_connect(sock, address):
            # Test-only wiring: prove the requested destination, then route it
            # to our local TLS fixture without contacting the real provider.
            state['connections'].append(address)
            assert address == ('1.1.1.1', 443)
            return original(sock, server.server_address)
        monkeypatch.setattr(socket.socket, 'connect', local_connect)
        thread = threading.Thread(target=server.serve_forever); thread.start()
        try: yield certfile, state
        finally: server.shutdown(); thread.join(5)


def binding(provider, *, trust=True, seconds=3, requests=1, request_authority=None):
    certfile, _ = provider
    result = CodexHTTPSUpstream('1.1.1.1', 'synthetic-token', 'synthetic-account', seconds=seconds, requests=requests, request_authority=request_authority)
    if trust: result._tls.load_verify_locations(cafile=str(certfile))
    return result


def test_verified_tls_fixed_destination_and_credential(provider, monkeypatch):
    monkeypatch.setenv('HTTPS_PROXY', 'http://127.0.0.1:1')
    adapter = binding(provider)
    assert adapter(b'{}') == b'data: {}\n\n'
    _, state = provider
    assert state['connections'] == [('1.1.1.1', 443)]
    path, headers, body = state['seen'][0]
    assert path == '/backend-api/codex/responses' and body == b'{}'
    assert headers['Host'] == 'chatgpt.com'
    assert headers['Authorization'] == 'Bearer synthetic-token'
    assert headers['ChatGPT-Account-Id'] == 'synthetic-account'
    with pytest.raises(Denied): adapter(b'{}')
    assert len(state['connections']) == 1


def test_untrusted_certificate_receives_no_http_credentials(provider):
    with pytest.raises(Denied): binding(provider, trust=False)(b'{}')
    assert provider[1]['seen'] == []


def test_hostname_mismatch_receives_no_http_credentials(provider):
    adapter = binding(provider)
    adapter._host = 'wrong.invalid'  # Trusted test fault, not a guest option.
    with pytest.raises(Denied): adapter(b'{}')
    assert provider[1]['seen'] == []


@pytest.mark.parametrize('status', [301, 302, 307, 308, 401, 403])
def test_redirect_or_auth_failure_never_retried(provider, status):
    provider[1]['status'] = status
    with pytest.raises(Denied): binding(provider)(b'{}')
    assert len(provider[1]['connections']) == 1
    assert len(provider[1]['seen']) == 1


@pytest.mark.parametrize('address', ['127.0.0.1', '10.0.0.1', '100.64.0.1', '169.254.169.254',
    '::1', 'fe80::1', 'fc00::1', '::ffff:8.8.8.8', '224.0.0.1', 'chatgpt.com'])
def test_nonpublic_or_nonliteral_address_rejected(address):
    with pytest.raises(ValueError):
        CodexHTTPSUpstream(address, 'synthetic-token', 'account', seconds=1, requests=1)


def test_chunked_sse_is_decoded(provider):
    provider[1].update(framing=[('Transfer-Encoding', 'chunked')],
                       wire=b'5\r\ndata:\r\n5\r\n {}\n\n\r\n0\r\n\r\n')
    assert binding(provider)(b'{}') == b'data: {}\n\n'


@pytest.mark.parametrize('framing,wire', [
    ([('Transfer-Encoding', 'chunked'), ('Content-Length', '0')], b'0\r\n\r\n'),
    ([('Transfer-Encoding', 'chunked'), ('Transfer-Encoding', 'chunked')], b'0\r\n\r\n'),
    ([('Transfer-Encoding', 'gzip, chunked')], b'0\r\n\r\n'),
    ([('Transfer-Encoding', 'chunked')], b'not-hex\r\n'),
    ([('Transfer-Encoding', 'chunked')], b'a\r\nshort'),
    ([('Transfer-Encoding', 'chunked')], b'5\r\nhello\r\n'),
    ([('Transfer-Encoding', 'chunked')], b'a\r\nsynthetic-\r\n5\r\ntoken\r\n0\r\n\r\n'),
])
def test_invalid_or_secret_bearing_chunks_are_rejected(provider, framing, wire):
    provider[1].update(framing=framing, wire=wire)
    with pytest.raises(Denied): binding(provider)(b'{}')


def test_chunked_size_limit(provider):
    data = b'x' * (8 * 1024 * 1024 + 1)
    provider[1].update(framing=[('Transfer-Encoding', 'chunked')],
                       wire=f'{len(data):x}\r\n'.encode() + data + b'\r\n0\r\n\r\n')
    with pytest.raises(Denied): binding(provider)(b'{}')


def test_continuous_tls_chunks_stop_at_deadline(provider):
    provider[1].update(framing=[('Transfer-Encoding', 'chunked')], drip=True)
    adapter = binding(provider, seconds=.3)
    start = time.monotonic()
    with pytest.raises(Denied): adapter(b'{}')
    assert time.monotonic() - start < 1.5
    with pytest.raises(Denied): adapter(b'{}')
    assert len(provider[1]['connections']) == 1


@pytest.mark.parametrize('value', ['text/event-stream; charset=utf-8',
    'Text/Event-Stream; Charset="UTF-8"'])
def test_utf8_sse_content_type(provider, value):
    provider[1]['content_types'] = [value]
    assert binding(provider)(b'{}') == b'data: {}\n\n'


@pytest.mark.parametrize('values', [[], ['text/html'],
    ['text/event-stream', 'text/event-stream'],
    ['text/event-stream; charset=iso-8859-1'],
    ['text/event-stream; charset=utf-8; charset=utf-8']])
def test_ambiguous_or_unsupported_content_type(provider, values):
    provider[1]['content_types'] = values
    with pytest.raises(Denied): binding(provider)(b'{}')


def test_missing_media_type_requires_complete_responses_stream(provider):
    wire = b'data: {"type":"response.completed","response":{"status":"completed","output":[]}}\n\n'
    provider[1].update(content_types=[], framing=[('Content-Length', str(len(wire)))], wire=wire)
    assert binding(provider)(b'{}') == wire


@pytest.mark.parametrize('wire', [
    b'<html>not a stream</html>',
    b'data: {"type":"response.created"}\n\n',
    b'data: {"type":"response.completed","response":{"status":"failed","output":[]}}\n\n',
    b'event: response.created\ndata: {"type":"response.completed","response":{"status":"completed","output":[]}}\n\n',
    b'data: {"type":"response.completed","type":"response.completed","response":{"status":"completed","output":[]}}\n\n',
])
def test_missing_media_type_rejects_nonresponses_or_incomplete_stream(provider, wire):
    provider[1].update(content_types=[], framing=[('Content-Length', str(len(wire)))], wire=wire)
    with pytest.raises(Denied): binding(provider)(b'{}')


def test_explicit_revocation_interrupts_tls_and_cannot_be_revived(provider):
    state = provider[1]
    state.update(framing=[('Transfer-Encoding', 'chunked')], drip=True)
    adapter = binding(provider, seconds=10, requests=2)
    results = []
    def request():
        try:
            results.append(adapter(b'{}'))
        except Denied:
            results.append('denied')
    thread = threading.Thread(target=request)
    thread.start()
    try:
        assert state['started'].wait(2)
        with pytest.raises(Denied):
            adapter.replace_credential('replacement-during-request')
        started = time.monotonic()
        adapter.revoke()
        thread.join(1)
        assert not thread.is_alive()
        assert time.monotonic() - started < 1
        assert results == ['denied']
        with pytest.raises(Denied):
            adapter.replace_credential('replacement-after-stop')
        with pytest.raises(Denied):
            adapter(b'{}')
        assert len(state['connections']) == len(state['seen']) == 1
    finally:
        adapter.revoke(); thread.join(2)


def test_trusted_rotation_keeps_tls_account_destination_and_request_budget(provider):
    adapter = binding(provider, requests=2)
    assert adapter(b'{}') == b'data: {}\n\n'
    deadline = adapter._deadline
    adapter.replace_credential('synthetic-replacement')
    assert adapter._deadline == deadline
    assert adapter(b'{}') == b'data: {}\n\n'
    with pytest.raises(Denied):
        adapter(b'{}')
    state = provider[1]
    assert [headers['Authorization'] for _, headers, _ in state['seen']] == [
        'Bearer synthetic-token', 'Bearer synthetic-replacement']
    assert all(path == '/backend-api/codex/responses' and
               headers['ChatGPT-Account-Id'] == 'synthetic-account'
               for path, headers, _ in state['seen'])
    assert state['connections'] == [('1.1.1.1', 443)] * 2


@pytest.mark.parametrize('reflected', ['synthetic-token', 'synthetic-rotated-token'])
def test_rotation_does_not_allow_current_or_retired_token_in_response(provider, reflected):
    adapter = binding(provider, seconds=5, requests=3)
    assert adapter(b'{}') == b'data: {}\n\n'
    deadline = adapter._deadline
    adapter.replace_credential('synthetic-rotated-token')
    _, state = provider
    wire = ('data: {"text":"' + reflected + '"}\n\n').encode()
    state.update(wire=wire, framing=[('Content-Length', str(len(wire)))])
    with pytest.raises(Denied, match='upstream body rejected') as error:
        adapter(b'{}')
    assert reflected not in str(error.value)
    assert state['seen'][-1][1]['Authorization'] == 'Bearer synthetic-rotated-token'
    assert adapter._deadline == deadline and adapter._remaining == 1
    # A rejected reflection consumes its call but does not disable useful inference.
    state.update(wire=b'data: {}\n\n', framing=[('Content-Length', '10')])
    assert adapter(b'{}') == b'data: {}\n\n'
    with pytest.raises(Denied):
        adapter(b'{}')
    assert len(state['seen']) == 3


def test_recreated_https_adapter_cannot_refill_persisted_authority(provider, tmp_path):
    import sys
    if sys.platform != 'linux':
        pytest.skip('Linux boot-bound request accounting')
    from daia.request_ledger import create
    path = tmp_path / 'authority.json'
    identifier = 'd' * 64
    create(path, identifier, seconds=30, requests=2)
    authority = (str(path), identifier)
    assert binding(provider, requests=6, request_authority=authority)(b'{}') == b'data: {}\n\n'
    # A failed provider attempt is also spent before another adapter is created.
    provider[1]['status'] = 503
    with pytest.raises(Denied):
        binding(provider, requests=6, request_authority=authority)(b'{}')
    provider[1]['status'] = 200
    with pytest.raises(Denied, match='Persisted request authority unavailable'):
        binding(provider, requests=6, request_authority=authority)(b'{}')
    assert len(provider[1]['connections']) == len(provider[1]['seen']) == 2

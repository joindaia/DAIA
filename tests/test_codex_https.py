import datetime
import http.server
import socket
import ssl
import threading

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
    state = {'status': 200, 'seen': [], 'connections': []}
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            state['seen'].append((self.path, dict(self.headers), body))
            self.send_response(state['status'])
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', '10')
            self.send_header('Location', 'https://example.invalid/account')
            self.end_headers(); self.wfile.write(b'data: {}\n\n')
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


def binding(provider, *, trust=True):
    certfile, _ = provider
    result = CodexHTTPSUpstream('1.1.1.1', 'synthetic-token', 'synthetic-account', seconds=3, requests=1)
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

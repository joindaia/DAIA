import socket
from unittest.mock import Mock

import pytest

from daia.public_egress import Denied, connect_public, read_connect


def answer(ip):
    family = socket.AF_INET6 if ':' in ip else socket.AF_INET
    addr = (ip, 443, 0, 0) if family == socket.AF_INET6 else (ip, 443)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', addr)


@pytest.mark.parametrize('ip', ['127.0.0.1','10.1.2.3','100.64.0.1','169.254.169.254','192.168.1.2','224.0.0.1','::1','fd00::1','fe80::1','ff02::1','::ffff:127.0.0.1','64:ff9b::a00:1','2002:7f00:1::','2001::1'])
def test_rejects_entire_mixed_dns_set_before_dial(monkeypatch, ip):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[answer('93.184.216.34'),answer(ip)])
    factory=Mock();monkeypatch.setattr(socket,'socket',factory)
    with pytest.raises(Denied):connect_public('docs.example:443',frozenset({'docs.example'}))
    factory.assert_not_called()


def test_connect_pins_numeric_address_without_second_dns(monkeypatch):
    resolver=Mock(return_value=[answer('93.184.216.34')]);monkeypatch.setattr(socket,'getaddrinfo',resolver)
    stream=Mock();stream.getpeername.return_value=('93.184.216.34',443)
    monkeypatch.setattr(socket,'socket',Mock(return_value=stream))
    assert connect_public('docs.example:443',frozenset({'docs.example'})) is stream
    stream.connect.assert_called_once_with(('93.184.216.34',443));resolver.assert_called_once()


def test_operator_exclusion_blocks_public_host_network(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[answer('93.184.216.34')])
    with pytest.raises(Denied):connect_public('docs.example:443',frozenset({'docs.example'}),['93.184.216.0/24'])


@pytest.mark.parametrize('authority',['docs.example:80','DOCS.example:443','docs.example.:443','127.0.0.1:443','docs.example@127.0.0.1:443','other.example:443','docs.example:0443'])
def test_authority_rejected_before_dns(monkeypatch,authority):
    resolver=Mock();monkeypatch.setattr(socket,'getaddrinfo',resolver)
    with pytest.raises(Denied):connect_public(authority,frozenset({'docs.example'}))
    resolver.assert_not_called()


def test_connect_header_does_not_consume_tls_bytes():
    a,b=socket.socketpair()
    try:
        b.sendall(b'CONNECT docs.example:443 HTTP/1.1\r\nHost: docs.example:443\r\n\r\nTLS')
        assert read_connect(a)=='docs.example:443'
        assert a.recv(3)==b'TLS'
    finally:a.close();b.close()


def test_connect_body_is_not_accepted():
    a,b=socket.socketpair()
    try:
        b.sendall(b'CONNECT docs.example:443 HTTP/1.1\r\nContent-Length: 1\r\n\r\nx')
        with pytest.raises(Denied):read_connect(a)
    finally:a.close();b.close()


def test_half_close_preserves_response_direction():
    import threading
    from daia.public_egress import tunnel
    client, proxy_client = socket.socketpair()
    proxy_upstream, server = socket.socketpair()
    errors = []
    def relay():
        try: tunnel(proxy_client, proxy_upstream, seconds=2)
        except Exception as exc: errors.append(exc)
    thread = threading.Thread(target=relay)
    for stream in (client, server): stream.settimeout(2)
    thread.start()
    try:
        client.sendall(b'request');client.shutdown(socket.SHUT_WR)
        assert server.recv(7) == b'request'
        assert server.recv(1) == b''
        server.sendall(b'response');server.shutdown(socket.SHUT_WR)
        assert client.recv(8) == b'response'
        assert client.recv(1) == b''
        thread.join(2)
        assert not thread.is_alive() and not errors
    finally:
        for stream in (client,proxy_client,proxy_upstream,server):stream.close()
        thread.join(2)


def test_peer_mismatch_closes_socket(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[answer('93.184.216.34')])
    stream=Mock();stream.getpeername.return_value=('127.0.0.1',443)
    monkeypatch.setattr(socket,'socket',Mock(return_value=stream))
    with pytest.raises(Denied):connect_public('docs.example:443',frozenset({'docs.example'}))
    stream.close.assert_called_once()


def test_header_size_limit():
    a,b=socket.socketpair()
    try:
        b.sendall(b'X'*4096)
        with pytest.raises(Denied,match='header limit'):read_connect(a)
    finally:a.close();b.close()


def test_tunnel_byte_limit_and_idle_deadline():
    import threading
    from daia.public_egress import tunnel
    for payload,limit,expected in [(b'0123456789',4,b'0123'),(b'',4,b'')]:
        client,pc=socket.socketpair();pu,server=socket.socketpair();errors=[]
        def relay():
            try:tunnel(pc,pu,seconds=.1,max_bytes=limit)
            except Exception as exc:errors.append(exc)
            finally:pc.close();pu.close()
        thread=threading.Thread(target=relay);thread.start();server.settimeout(2)
        try:
            if payload:client.sendall(payload)
            received=bytearray()
            while chunk:=server.recv(32):received.extend(chunk)
            thread.join(2)
            assert not thread.is_alive() and not errors and bytes(received)==expected
        finally:client.close();server.close();thread.join(2)


def test_canary_refuses_host_network_before_binding(monkeypatch):
    from pathlib import Path
    import runpy
    main = runpy.run_path(str(Path(__file__).parents[1] /
        'scripts/probe_public_egress_canary.py'))['main']
    monkeypatch.setattr(socket, 'if_nameindex', lambda: [(1, 'lo'), (2, 'eth0')])
    factory = Mock(); monkeypatch.setattr(socket, 'socket', factory)
    with pytest.raises(RuntimeError, match='network namespace'):
        main()
    factory.assert_not_called()

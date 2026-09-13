"""Credential-free DNS-result canary. Run only in an isolated network namespace.

Requires free IPv4/IPv6 loopback port 443. Uses synthetic resolver answers but real
TCP listeners; no Internet requests. Does not test a wire-level DNS server or VM.
"""
import json
import select
import socket
import threading

from daia.public_egress import handle_connection


def main():
    if {name for _, name in socket.if_nameindex()} != {'lo'}:
        raise RuntimeError('Dedicated loopback-only network namespace required')
    real_socket, real_resolver = socket.socket, socket.getaddrinfo
    listeners = []
    try:
        for family, address in ((socket.AF_INET, ('127.0.0.1', 443)),
                                (socket.AF_INET6, ('::1', 443, 0, 0))):
            server = real_socket(family, socket.SOCK_STREAM)
            listeners.append(server)
            if family == socket.AF_INET6:
                server.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            server.bind(address); server.listen(8)

        def control():
            for server in listeners:
                with real_socket(server.family, socket.SOCK_STREAM) as client:
                    client.settimeout(1); client.connect(server.getsockname())
                    client.sendall(b'canary-control')
                    conn, _ = server.accept()
                    with conn:
                        conn.settimeout(1)
                        assert conn.recv(64) == b'canary-control'

        def answer(ip):
            family = socket.AF_INET6 if ':' in ip else socket.AF_INET
            address = (ip,443,0,0) if family == socket.AF_INET6 else (ip,443)
            return (family,socket.SOCK_STREAM,socket.IPPROTO_TCP,'',address)

        controls = 0
        results = []
        for addresses in (['127.0.0.1'], ['::1'], ['1.1.1.1','127.0.0.1'],
                          ['1.1.1.1','::1'], ['127.0.0.1','1.1.1.1'],
                          ['::1','2606:4700:4700::1111']):
            control(); controls += 2
            attempts, resolutions = [], []
            class TracedSocket(real_socket):
                def connect(self, address):
                    attempts.append(address)
                    return super().connect(address)
            def resolve(host, port, **kwargs):
                assert host == 'research.daia.invalid' and port == 443
                resolutions.append(True)
                return [answer(ip) for ip in addresses]
            client, gateway = socket.socketpair()
            thread = None
            try:
                socket.socket, socket.getaddrinfo = TracedSocket, resolve
                thread = threading.Thread(target=handle_connection,
                    args=(gateway,frozenset({'research.daia.invalid'})))
                thread.start()
                client.settimeout(2)
                client.sendall(b'CONNECT research.daia.invalid:443 HTTP/1.1\r\nHost: research.daia.invalid:443\r\n\r\n')
                reply = b''
                while chunk := client.recv(4096): reply += chunk
                thread.join(2)
                assert not thread.is_alive()
                assert reply.startswith(b'HTTP/1.1 403')
                assert len(resolutions) == 1 and not attempts
                assert not select.select(listeners, [], [], 0)[0]
            finally:
                socket.socket, socket.getaddrinfo = real_socket, real_resolver
                client.close(); gateway.close()
                if thread is not None: thread.join(2)
            control(); controls += 2
            results.append({'dns_answers':addresses,'http_403':True,
                            'outbound_connect_attempts':0,'canary_connections':0})
        print(json.dumps({'synthetic_dns_answers':True,'real_tcp_canaries':True,
                          'positive_control_connections':controls,'cases':results}))
    finally:
        socket.socket, socket.getaddrinfo = real_socket, real_resolver
        for server in listeners: server.close()


if __name__ == '__main__':
    main()

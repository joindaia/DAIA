"""Credential-free wire-DNS probe, only in a private lab network/mount namespace.

Requires loopback aliases 1.1.1.1 and 2606:4700:4700::1111, local resolver
127.0.0.1, and free ports 53/443. These addresses stay inside the namespace.
Minimal DNS fixture for controlled libc queries, never an Internet DNS service.
"""
import ipaddress
import json
from pathlib import Path
import select
import socket
import socketserver
import struct
import threading
from daia.public_egress import connect_public, Denied


def name_wire(name):
    return b''.join(bytes([len(part)]) + part.encode() for part in name.split('.')) + b'\0'


def main():
    if {n for _, n in socket.if_nameindex()} != {'lo'}:
        raise RuntimeError('Dedicated loopback-only network namespace required')
    if 'nameserver 127.0.0.1' not in Path('/etc/resolv.conf').read_text():
        raise RuntimeError('Private local DNS resolver required')
    cases = {
        'public.daia.invalid': (None, ['1.1.1.1']),
        'mixed4.daia.invalid': (None, ['1.1.1.1', '127.0.0.1']),
        'mixed6.daia.invalid': (None, ['2606:4700:4700::1111', '::1']),
        'mixedboth.daia.invalid': (None, ['1.1.1.1', '::1']),
        'aliasprivate.daia.invalid': ('private-target.daia.invalid', ['127.0.0.1', '::1']),
        'aliaspublic.daia.invalid': ('public-target.daia.invalid', ['1.1.1.1']),
    }
    queries = []
    class DNS(socketserver.BaseRequestHandler):
        def handle(self):
            data, server = self.request
            offset = 12; labels = []
            while data[offset]:
                size = data[offset]; assert 0 < size < 64
                labels.append(data[offset+1:offset+size+1].decode('ascii')); offset += size + 1
            offset += 1
            kind, cls = struct.unpack('!HH', data[offset:offset+4]); offset += 4
            name = '.'.join(labels); assert name in cases and cls == 1
            alias, addresses = cases[name]; records = []
            if alias:
                value = name_wire(alias)
                records.append(b'\xc0\x0c' + struct.pack('!HHIH', 5, 1, 0, len(value)) + value)
            for text in addresses:
                ip = ipaddress.ip_address(text)
                if kind == (1 if ip.version == 4 else 28):
                    owner = name_wire(alias) if alias else b'\xc0\x0c'
                    records.append(owner + struct.pack('!HHIH', kind, 1, 0, len(ip.packed)) + ip.packed)
            queries.append({'name': name, 'type': kind, 'cname': bool(alias), 'answers': len(records)})
            packet = data[:2] + struct.pack('!HHHHH', 0x8180, 1, len(records), 0, 0)
            server.sendto(packet + data[12:offset] + b''.join(records), self.client_address)
    listeners = []
    with socketserver.UDPServer(('127.0.0.1', 53), DNS) as dns:
        thread = threading.Thread(target=dns.serve_forever, daemon=True); thread.start()
        try:
            for family, ip in ((socket.AF_INET,'127.0.0.1'), (socket.AF_INET6,'::1'),
                               (socket.AF_INET,'1.1.1.1'), (socket.AF_INET6,'2606:4700:4700::1111')):
                listener = socket.socket(family, socket.SOCK_STREAM)
                if family == socket.AF_INET6:
                    listener.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                listener.bind((ip,443)); listener.listen(8); listener.settimeout(1); listeners.append(listener)
            controls = 0; results = []
            for name in cases:
                for listener in listeners:
                    with socket.socket(listener.family, socket.SOCK_STREAM) as client:
                        client.settimeout(1); client.connect(listener.getsockname())
                        connection, _ = listener.accept(); connection.close(); controls += 1
                if name.startswith(('public.', 'aliaspublic.')):
                    with connect_public(name+':443', frozenset(cases)) as client:
                        connection, _ = listeners[2].accept(); connection.close()
                    results.append({'name':name, 'public_connection':True})
                else:
                    try:
                        stream = connect_public(name+':443', frozenset(cases))
                    except Denied:
                        pass
                    else:
                        stream.close(); raise AssertionError('Private DNS set accepted')
                    results.append({'name':name, 'denied':True})
                assert not select.select(listeners, [], [], .05)[0], 'Unexpected canary connection'
            assert {q['type'] for q in queries} >= {1,28}
            print(json.dumps({'wire_dns':True, 'mocked_resolver':False,
                'positive_controls':controls, 'unexpected_connections':0,
                'cases':results, 'queries':queries}))
        finally:
            for listener in listeners: listener.close()
            dns.shutdown(); thread.join(2)


if __name__ == '__main__':
    main()

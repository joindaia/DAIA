"""Credential-free real curl/TLS redirect test in an isolated lab namespace.

Requires loopback-only networking, local 1.1.1.1 alias and private hosts entries:
public.daia.invalid=1.1.1.1, private4.daia.invalid=127.0.0.1,
private6.daia.invalid=::1. Never run on a production proxy. Uses temporary TLS keys.
This tests the research CONNECT transport, not a browser or whole KVM worker.
"""
import http.server
import json
from pathlib import Path
import select
import socket
import socketserver
import ssl
import subprocess
import tempfile
import threading
from daia.public_egress import handle_connection


def main():
    if {n for _, n in socket.if_nameindex()} != {'lo'}:
        raise RuntimeError('Dedicated loopback-only namespace required')
    expected = {'public.daia.invalid':'1.1.1.1',
                'private4.daia.invalid':'127.0.0.1', 'private6.daia.invalid':'::1'}
    for name, ip in expected.items():
        records = socket.getaddrinfo(name,443,type=socket.SOCK_STREAM,proto=socket.IPPROTO_TCP)
        if {r[4][0] for r in records} != {ip}:
            raise RuntimeError('Private lab hosts mapping required')
    redirects = {'/public':'https://public.daia.invalid/ok',
                 '/private4':'https://private4.daia.invalid/secret',
                 '/private6':'https://private6.daia.invalid/secret',
                 '/literal':'https://127.0.0.1/secret',
                 '/unknown':'https://unlisted.daia.invalid/secret'}
    requests = []
    class HTTPS(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            if self.path == '/ok':
                self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
            else:
                self.send_response(302)
                self.send_header('Location',redirects[self.path]); self.end_headers()
        def log_message(self,*args): pass
    class Proxy(socketserver.BaseRequestHandler):
        def handle(self): handle_connection(self.request,frozenset(expected))
    class Server(socketserver.ThreadingMixIn,socketserver.TCPServer):
        daemon_threads=True
    listeners=[]
    try:
        for family,address in ((socket.AF_INET,('127.0.0.1',443)),(socket.AF_INET6,('::1',443))):
            s=socket.socket(family,socket.SOCK_STREAM)
            if family==socket.AF_INET6: s.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,1)
            s.bind(address);s.listen(8);s.settimeout(1);listeners.append(s)
        with tempfile.TemporaryDirectory(prefix='daia-redirect-tls-') as folder:
            root=Path(folder); cert=root/'cert.pem'; key=root/'key.pem'
            subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
                '-subj','/CN=public.daia.invalid','-addext','subjectAltName=DNS:public.daia.invalid',
                '-keyout',str(key),'-out',str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            with http.server.ThreadingHTTPServer(('1.1.1.1',443),HTTPS) as upstream, Server(('127.0.0.1',0),Proxy) as proxy:
                context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.load_cert_chain(cert,key)
                upstream.socket=context.wrap_socket(upstream.socket,server_side=True)
                threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in (upstream,proxy)]
                for t in threads:t.start()
                results=[];controls=0
                try:
                    for path in redirects:
                        for listener in listeners:
                            with socket.create_connection(listener.getsockname()[:2],timeout=1):
                                conn,_=listener.accept();conn.close();controls+=1
                        r=subprocess.run(['curl','--silent','--show-error','--fail','--location',
                            '--max-redirs','2','--max-time','5','--noproxy','',
                            '--proxy',f'http://127.0.0.1:{proxy.server_address[1]}',
                            '--cacert',str(cert),'https://public.daia.invalid'+path],
                            env={'PATH':'/usr/bin:/bin','HOME':folder},capture_output=True,timeout=8)
                        if path=='/public':
                            if r.returncode or r.stdout!=b'ok':raise RuntimeError('Public redirect failed')
                        elif r.returncode==0 or b'403' not in r.stderr:
                            raise RuntimeError('Redirect not explicitly denied by proxy')
                        if select.select(listeners,[],[],.05)[0]:raise RuntimeError('Private canary reached')
                        if path not in requests:raise RuntimeError('Redirect response not exercised')
                        results.append({'path':path,'public_success':path=='/public','proxy_denied':path!='/public'})
                    print(json.dumps({'real_curl':True,'tls_verified':True,'mocked_resolver':False,
                        'wire_dns':False,'positive_canary_controls':controls,'unexpected_canary_connections':0,
                        'https_requests':len(requests),'cases':results,'whole_worker_test':False}))
                finally:
                    upstream.shutdown();proxy.shutdown()
                    for t in threads:t.join(2)
    finally:
        for s in listeners:s.close()


if __name__=='__main__':main()

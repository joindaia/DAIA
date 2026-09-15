"""Test-only research listener used by the KVM egress canary trial.

Requires the private lab harness: isolated network namespace, hosts-file entries
v4.daia.invalid -> 127.0.0.1 and v6.daia.invalid -> ::1, exact-name allowlist,
fixed Unix relay and CAP_NET_BIND_SERVICE solely for the test listeners on 443.
Do not replace a production gateway with this fixture. No provider credentials.
The root launcher observes this report outside the guest before terminating the
controller. This file alone does not launch the VM or configure its boundaries.
"""
import socket,socketserver,threading,os,sys,json,select
from pathlib import Path
sys.path.insert(0,'/var/lib/daia-lab/templates')
from public_egress import handle_connection
policy=json.load(open('/var/lib/daia-lab/templates/egress-policy.json'))
listeners=[]
for family,addr in [(socket.AF_INET,('127.0.0.1',443)),(socket.AF_INET6,('::1',443))]:
 s=socket.socket(family,socket.SOCK_STREAM)
 if family==socket.AF_INET6:s.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,1)
 s.bind(addr);s.listen(8);listeners.append(s)
report={'handled':0,'control_connections':0,'unexpected_connections':0,'os_resolver_hosts_file':True,'wire_dns':False}
report['resolved_addresses']={}
for host,expected in [('v4.daia.invalid','127.0.0.1'),('v6.daia.invalid','::1')]:
 addresses={r[4][0] for r in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM,proto=socket.IPPROTO_TCP)}
 assert addresses=={expected}
 report['resolved_addresses'][host]=sorted(addresses)
lock=threading.Lock()
def control():
 for server in listeners:
  with socket.create_connection(server.getsockname()[:2],timeout=2) as client:
   client.sendall(b'control')
   conn,_=server.accept()
   with conn:
    conn.settimeout(2);assert conn.recv(64)==b'control'
  report['control_connections']+=1
class Handler(socketserver.BaseRequestHandler):
 def handle(self):
  with lock:
   control()
   handle_connection(self.request,frozenset(policy['allowed']),policy['excluded'])
   ready=select.select(listeners,[],[],0)[0]
   report['unexpected_connections']+=len(ready)
   assert not ready
   control();report['handled']+=1
   Path('/run/daia-research/canary-report.json').write_text(json.dumps(report))
class Server(socketserver.ThreadingMixIn,socketserver.UnixStreamServer):
 daemon_threads=True
with Server('/run/daia-research/gateway.sock',Handler) as server:
 os.chmod('/run/daia-research/gateway.sock',0o660);server.serve_forever()

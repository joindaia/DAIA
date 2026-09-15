"""Test-only DNS rebinding fixture; never run as a production gateway.

Run via the DAIA private KVM lab in its dedicated service network namespace.
Requires loopback aliases 1.1.1.1/32 and 2606:4700:4700::1111/128 configured by
trusted namespace setup, hosts: dns, resolver 127.0.0.1, and CAP_NET_BIND_SERVICE
solely for fixture listeners on 53/443. No external interface or default route.
Allow rebind4.daia.invalid and rebind6.daia.invalid in the test egress policy.
The guest issues an initial forbidden GET, then public/private CONNECT requests
for v4 and v6 in order. The external launcher validates this report and cgroup,
overlay and endpoint cleanup. This fixture alone does not launch or isolate a VM.
DNS is deliberately a minimal parser for the controlled libc queries in this
lab, not a DNS implementation for untrusted network deployment.
"""
import socket,socketserver,threading,os,sys,json,select,struct,ipaddress
from pathlib import Path
sys.path.insert(0,'/var/lib/daia-lab/templates')
from public_egress import handle_connection
policy=json.load(open('/var/lib/daia-lab/templates/egress-policy.json'))
phases={'rebind4.daia.invalid':False,'rebind6.daia.invalid':False}
report={'handled':0,'control_connections':0,'unexpected_connections':0,'wire_dns':True,'dns_queries':[],'public_connections':{'4':0,'6':0}}
class DNS(socketserver.BaseRequestHandler):
 def handle(self):
  data,server=self.request
  offset=12;labels=[]
  while data[offset]:
   length=data[offset];assert 0<length<64
   labels.append(data[offset+1:offset+1+length].decode('ascii'));offset+=length+1
  offset+=1;kind,cls=struct.unpack('!HH',data[offset:offset+4]);offset+=4
  name='.'.join(labels);assert name in phases and cls==1
  private=phases[name]
  ip=('127.0.0.1' if private else '1.1.1.1') if name.startswith('rebind4') else ('::1' if private else '2606:4700:4700::1111')
  value=ipaddress.ip_address(ip);wanted=1 if value.version==4 else 28
  answer=b''
  if kind==wanted:
   answer=b'\xc0\x0c'+struct.pack('!HHIH',kind,1,0,len(value.packed))+value.packed
  report['dns_queries'].append({'name':name,'type':kind,'private_phase':private,'answers':[ip] if answer else []})
  packet=data[:2]+struct.pack('!HHHHH',0x8180,1,int(bool(answer)),0,0)+data[12:offset]+answer
  server.sendto(packet,self.client_address)
dns=socketserver.UDPServer(('127.0.0.1',53),DNS)
threading.Thread(target=dns.serve_forever,daemon=True).start()
listeners=[]
for family,addr in [(socket.AF_INET,('127.0.0.1',443)),(socket.AF_INET6,('::1',443))]:
 s=socket.socket(family,socket.SOCK_STREAM)
 if family==socket.AF_INET6:s.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,1)
 s.bind(addr);s.listen(8);listeners.append(s)
def public_server(family,ip,key):
 s=socket.socket(family,socket.SOCK_STREAM);s.bind((ip,443));s.listen(2)
 def serve():
  with s:
   conn,_=s.accept()
   with conn:
    report['public_connections'][key]+=1;conn.sendall(b'public-canary-'+key.encode())
 threading.Thread(target=serve,daemon=True).start()
public_server(socket.AF_INET,'1.1.1.1','4')
public_server(socket.AF_INET6,'2606:4700:4700::1111','6')
lock=threading.Lock()
def control():
 for server in listeners:
  with socket.create_connection(server.getsockname()[:2],timeout=2) as client:
   client.sendall(b'control');conn,_=server.accept()
   with conn:
    conn.settimeout(2);assert conn.recv(64)==b'control'
  report['control_connections']+=1
class Handler(socketserver.BaseRequestHandler):
 def handle(self):
  with lock:
   if report['handled']==2:phases['rebind4.daia.invalid']=True
   if report['handled']==4:phases['rebind6.daia.invalid']=True
   control();handle_connection(self.request,frozenset(policy['allowed']),policy['excluded'])
   ready=select.select(listeners,[],[],0)[0];report['unexpected_connections']+=len(ready);assert not ready
   control();report['handled']+=1
   Path('/run/daia-research/canary-report.json').write_text(json.dumps(report))
class Server(socketserver.ThreadingMixIn,socketserver.UnixStreamServer):daemon_threads=True
with Server('/run/daia-research/gateway.sock',Handler) as server:
 os.chmod('/run/daia-research/gateway.sock',0o660);server.serve_forever()

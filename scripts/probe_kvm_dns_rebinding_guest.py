"""Exact guest probe for the credential-free KVM DNS rebinding lab.

Requires the lab's three fixed relays. Ends in a readiness wait so the external
watcher can verify listeners and kill the controller; its watchdog is mandatory.
Run only in the disposable guest, never on the host.
"""
import socket,json,time,os
for host in ('10.0.2.101','10.0.2.102'):
 with socket.create_connection((host,3128),timeout=5) as s:
  s.sendall(b'GET /forbidden HTTP/1.1\r\nHost: forbidden\r\n\r\n')
  assert s.recv(100).startswith(b'HTTP/1.1 403')
for key in ('4','6'):
 host='rebind'+key+'.daia.invalid'
 for private in (False,True):
  with socket.create_connection(('10.0.2.102',3128),timeout=5) as conn:
   conn.sendall(('CONNECT '+host+':443 HTTP/1.1\r\nHost: '+host+':443\r\n\r\n').encode())
   reply=b''
   while chunk:=conn.recv(4096):reply+=chunk
   if private:assert reply.startswith(b'HTTP/1.1 403')
   else:
    assert reply.startswith(b'HTTP/1.1 200')
    assert reply.endswith(b'public-canary-'+key.encode())
s=socket.create_connection(('10.0.2.100',3128),timeout=5)
f=s.makefile('rwb',buffering=0)
f.write(json.dumps({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'DAIA-crash-lab','version':'1'}}}).encode()+b'\n')
while True:
 msg=json.loads(f.readline())
 if msg.get('id')==1:
  assert 'result' in msg;break
with open('/dev/ttyS0','w') as out:out.write('DAIA_CRASH_READY '+'24b5cf38fe1346a1a3b64bc6095bb786'+'\n')
if os.fork()==0:
 while True:time.sleep(1)
while True:time.sleep(1)

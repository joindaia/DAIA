"""Credential-free 34-second assignment relay liveness/expiry probe."""
import sys,socket,subprocess,threading,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from daia.assignment_relay import relay
client,peer=socket.socketpair();client.settimeout(3)
helper=subprocess.Popen([sys.executable,'-u','-c','import sys; line=sys.stdin.buffer.readline(); sys.stdout.buffer.write(line); sys.stdout.buffer.flush(); sys.stdin.buffer.read()'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
results=[];errors=[]
start=time.monotonic();deadline=start+34

def run():
 try:results.append(relay(peer,helper,seconds=150,deadline=deadline))
 except Exception as e:errors.append(type(e).__name__)
 finally:peer.close()
thread=threading.Thread(target=run);thread.start()
try:
 time.sleep(31)
 client.sendall(b'heartbeat\n');assert client.recv(10)==b'heartbeat\n'
 echo_elapsed=time.monotonic()-start
 thread.join(5)
 assert not thread.is_alive() and results==['timeout'] and not errors
 elapsed=time.monotonic()-start
 assert 33.5<=elapsed<36
 report={'echo_after_seconds':round(echo_elapsed,3),'fixed_deadline_seconds':34,'closed_after_seconds':round(elapsed,3),'deadline_not_reset_by_traffic':True,'provider_requests':0,'scope':'real socket and subprocess relay; no VM or native agent'}
 print(json.dumps(report))
finally:
 client.close();helper.kill();helper.communicate(timeout=3);thread.join(3)

"""Test-only subscription lab service; requires the controller isolation profile."""
import socketserver,threading,os,sys,json
sys.path.insert(0,'/var/lib/daia-lab/templates')
from public_egress import handle_connection
policy=json.load(open('/var/lib/daia-lab/templates/egress-policy.json'))
class Handler(socketserver.BaseRequestHandler):
 def handle(self):handle_connection(self.request,frozenset(policy['allowed']),policy['excluded'])
class Server(socketserver.ThreadingMixIn,socketserver.UnixStreamServer):
 daemon_threads=True
 slots=threading.BoundedSemaphore(8)
 def process_request(self,request,address):
  if not self.slots.acquire(blocking=False):request.close();return
  try:super().process_request(request,address)
  except BaseException:self.slots.release();raise
 def process_request_thread(self,request,address):
  try:super().process_request_thread(request,address)
  finally:self.slots.release()
 def handle_error(self,*args):pass
with Server('/run/daia-research/gateway.sock',Handler) as server:
 os.chmod('/run/daia-research/gateway.sock',0o660);server.serve_forever()

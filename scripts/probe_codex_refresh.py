import argparse
import selectors
import socket
import socketserver
import base64, hashlib, http.server, json, os, pathlib, subprocess, tempfile, threading, time
parser=argparse.ArgumentParser(description='Native Codex synthetic refresh/restart probe; uses no existing auth.')
parser.add_argument('binary',type=pathlib.Path)
parser.add_argument('--account-only',action='store_true',help='Use trusted native account/read without starting model work')
parser.add_argument('--binding',action='store_true',help='Use native auth on the trusted side of the local model channel')
parser.add_argument('--reject-refresh',action='store_true',help='Return synthetic revocation failure; requires account-only mode')
parser.add_argument('--force-refresh',action='store_true',help='Ask the native account interface to refresh explicitly')
args=parser.parse_args()
if args.binding and not args.account_only:parser.error('--binding requires --account-only')
if args.reject_refresh and not args.account_only:parser.error('--reject-refresh requires --account-only')
binary=str(args.binary.resolve())
assert hashlib.sha256(pathlib.Path(binary).read_bytes()).hexdigest()=='56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da'
def jwt(exp):
 def b(x):return base64.urlsafe_b64encode(json.dumps(x).encode()).decode().rstrip('=')
 return b({'alg':'none'})+'.'+b({'exp':exp,'https://api.openai.com/auth':{'chatgpt_account_id':'synthetic-account','chatgpt_plan_type':'plus'}})+'.synthetic'
new=jwt(int(time.time())+3600)
calls=[]
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):self.send_error(403)
 def do_CONNECT(self):self.send_error(403)
 def do_POST(self):
  raw=self.rfile.read(int(self.headers.get('Content-Length','0')))
  if self.path=='/oauth/token':
   body=json.loads(raw);assert body['refresh_token']=='synthetic-refresh'
   calls.append('refresh')
   if args.reject_refresh:
    data=b'{"error":{"code":"refresh_token_invalidated"}}'
    self.send_response(401);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
   data=json.dumps({'access_token':new,'refresh_token':'synthetic-rotated'}).encode();mime='application/json'
  elif self.path=='/v1/responses':
   calls.append('model-refreshed' if self.headers.get('Authorization')=='Bearer '+new else 'model-wrong-auth')
   item={'id':'msg_fixture','type':'message','role':'assistant','status':'completed','content':[{'type':'output_text','text':'DAIA_AUTH_READY','annotations':[]}]}
   response={'id':'resp_fixture','object':'response','status':'completed','output':[item],'usage':{'input_tokens':1,'output_tokens':1,'total_tokens':2}}
   events=[('response.created',{'response':{**response,'status':'in_progress','output':[]}}),
           ('response.output_item.added',{'output_index':0,'item':{**item,'status':'in_progress','content':[]}}),
           ('response.output_text.delta',{'item_id':item['id'],'output_index':0,'content_index':0,'delta':'DAIA_AUTH_READY'}),
           ('response.output_item.done',{'output_index':0,'item':item}),
           ('response.completed',{'response':response})]
   data=''.join('event: '+name+'\ndata: '+json.dumps({'type':name,**payload})+'\n\n' for name,payload in events).encode();mime='text/event-stream'
  else:self.send_error(403);return
  self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
server=http.server.HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 with tempfile.TemporaryDirectory(prefix='daia-refresh-') as root:
  home=pathlib.Path(root);url=f'http://127.0.0.1:{server.server_port}'
  auth=home/'auth.json';auth.write_text(json.dumps({'auth_mode':'chatgpt','tokens':{'id_token':jwt(int(time.time())+3600),'access_token':jwt(1),'refresh_token':'synthetic-refresh','account_id':'synthetic-account'},'last_refresh':'2026-09-01T00:00:00Z'}));auth.chmod(0o600)
  (home/'config.toml').write_text(f'''model = "daia-fixture"
model_provider = "lab"
cli_auth_credentials_store = "file"
[model_providers.lab]
name = "Synthetic auth lab"
base_url = "{url}/v1"
wire_api = "responses"
requires_openai_auth = true
supports_websockets = false
''')
  env={'PATH':'/usr/bin:/bin','HOME':root,'CODEX_HOME':root,'CODEX_REFRESH_TOKEN_URL_OVERRIDE':url+'/oauth/token','HTTP_PROXY':url,'HTTPS_PROXY':url,'NO_PROXY':'127.0.0.1'}
  exits=[]
  markers=[]
  admitted=[]
  for i in range(2):
   if args.account_only:
    p=subprocess.Popen([binary,'app-server'],env=env,cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    def send(value):p.stdin.write(json.dumps(value)+'\n');p.stdin.flush()
    def receive(wanted):
     deadline=time.monotonic()+20
     with selectors.DefaultSelector() as sel:
      sel.register(p.stdout,selectors.EVENT_READ)
      while time.monotonic()<deadline:
       if not sel.select(max(0,deadline-time.monotonic())):break
       line=p.stdout.readline()
       if not line:raise RuntimeError('app-server stopped')
       item=json.loads(line)
       if item.get('id')==wanted:
        assert 'error' not in item,item
        return item
     raise TimeoutError('app-server response')
    try:
     send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'daia-auth-lab','version':'0.1'}}});receive(1)
     send({'method':'initialized'})
     send({'id':2,'method':'account/read','params':{'refreshToken':args.force_refresh}})
     answer=receive(2)
     if args.binding:
      send({'id':3,'method':'getAuthStatus','params':{'includeToken':True,'refreshToken':False}})
      credential=receive(3)['result'].get('authToken')
      if args.reject_refresh:
       assert credential is None
       admitted.append(False)
      else:
       # Lab oracle: require the exact fixture-issued, refreshed token.
       assert credential==new
       from daia.model_upstream import LocalModelUpstream
       from daia.model_request import RequestGate
       from daia.model_channel import serve_once
       route=str(home/'model.sock')
       with socketserver.UnixStreamServer(route,Handler) as upstream:
        worker=threading.Thread(target=upstream.serve_forever);worker.start()
        binding=LocalModelUpstream(route,credential,seconds=5,requests=1)
        try:
         body=json.dumps({'model':'daia-fixture','store':False,'stream':True,'tools':[],'input':[{'role':'user','content':[{'type':'input_text','text':'hello'}]}]}).encode()
         client,channel=socket.socketpair()
         forwarder=threading.Thread(target=serve_once,args=(channel,RequestGate(body),binding));forwarder.start()
         with client:
          client.settimeout(5)
          client.sendall(b'POST /v1/responses HTTP/1.1\r\nHost: daia-model\r\nContent-Type: application/json\r\nContent-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body)
          reply=b''
          while chunk:=client.recv(65536):reply+=chunk
         forwarder.join(5)
         assert not forwarder.is_alive()
         assert reply.startswith(b'HTTP/1.1 200') and b'DAIA_AUTH_READY' in reply
         assert credential.encode() not in reply
         admitted.append(True)
        finally:
         binding.revoke();upstream.shutdown();worker.join(5)
       pathlib.Path(route).unlink()
     if not args.reject_refresh:assert answer['result']['account']['type']=='chatgpt',answer
    finally:
     p.stdin.close()
     try:p.wait(timeout=5)
     except subprocess.TimeoutExpired:p.kill();p.wait()
    exits.append(p.returncode)
    markers.append(True)
   else:
    p=subprocess.run([binary,'exec','--skip-git-repo-check','--ephemeral','--sandbox','read-only','--json','Return DAIA_AUTH_READY without using tools.'],env=env,cwd=root,capture_output=True,timeout=45)
    exits.append(p.returncode)
    markers.append(b"DAIA_AUTH_READY" in p.stdout)
    if p.returncode: print(p.stderr.decode()[-1500:])
  stored=json.loads(auth.read_text())
  result={'exits':exits,'markers':markers,'calls':calls,'rotated_persisted':stored['tokens']['refresh_token']=='synthetic-rotated','access_persisted':stored['tokens']['access_token']==new}
  if args.binding:
   result['bindings_admitted']=admitted
   assert admitted==[not args.reject_refresh]*2
  print(json.dumps(result))
  result.pop('bindings_admitted',None)
  if args.reject_refresh:
   assert exits==[0,0] and calls and set(calls)=={'refresh'}
   assert not result['rotated_persisted'] and not result['access_persisted']
   # Account metadata is not evidence of successful credential renewal.
   assert stored['tokens']['access_token']==jwt(1)
  else:assert result=={'exits':[0,0],'markers':[True,True],'calls':(['refresh'] if args.account_only and not args.binding else ['refresh','model-refreshed','model-refreshed']),'rotated_persisted':True,'access_persisted':True}
finally:server.shutdown();server.server_close();thread.join()

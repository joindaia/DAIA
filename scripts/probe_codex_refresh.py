import argparse
import base64, hashlib, http.server, json, os, pathlib, subprocess, tempfile, threading, time
parser=argparse.ArgumentParser(description='Native Codex synthetic refresh/restart probe; uses no existing auth.')
parser.add_argument('binary',type=pathlib.Path)
binary=str(parser.parse_args().binary.resolve())
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
   calls.append('refresh');data=json.dumps({'access_token':new,'refresh_token':'synthetic-rotated'}).encode();mime='application/json'
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
  for i in range(2):
   p=subprocess.run([binary,'exec','--skip-git-repo-check','--ephemeral','--sandbox','read-only','--json','Return DAIA_AUTH_READY without using tools.'],env=env,cwd=root,capture_output=True,timeout=45)
   exits.append(p.returncode)
   markers.append(b"DAIA_AUTH_READY" in p.stdout)
   if p.returncode: print(p.stderr.decode()[-1500:])
  stored=json.loads(auth.read_text())
  result={'exits':exits,'markers':markers,'calls':calls,'rotated_persisted':stored['tokens']['refresh_token']=='synthetic-rotated','access_persisted':stored['tokens']['access_token']==new}
  print(json.dumps(result));assert result=={'exits':[0,0],'markers':[True,True],'calls':['refresh','model-refreshed','model-refreshed'],'rotated_persisted':True,'access_persisted':True}
finally:server.shutdown();server.server_close();thread.join()

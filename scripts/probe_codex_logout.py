import argparse
import base64, hashlib, http.server, json, os, pathlib, subprocess, tempfile, threading
parser=argparse.ArgumentParser(description='Synthetic native Codex logout probe; never uses existing auth.')
parser.add_argument('binary', type=pathlib.Path)
binary=parser.parse_args().binary.resolve()
assert hashlib.sha256(binary.read_bytes()).hexdigest()=='56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da'
reports=[]
for status in (200,503):
 calls=[]
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args): pass
  def do_POST(self):
   body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
   calls.append({'path':self.path,'refresh_selected':body.get('token')=='synthetic-refresh','hint':body.get('token_type_hint')})
   self.send_response(status);self.send_header('Content-Length','0');self.end_headers()
 server=http.server.HTTPServer(('127.0.0.1',0),Handler)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 with tempfile.TemporaryDirectory(prefix='daia-auth-lab-') as root:
  home=pathlib.Path(root)
  def b64(x):return base64.urlsafe_b64encode(json.dumps(x).encode()).decode().rstrip('=')
  jwt=b64({'alg':'none'})+'.'+b64({'https://api.openai.com/auth':{'chatgpt_account_id':'synthetic-account','chatgpt_plan_type':'plus'}})+'.synthetic'
  auth=home/'auth.json'
  auth.write_text(json.dumps({'auth_mode':'chatgpt','OPENAI_API_KEY':None,'tokens':{'id_token':jwt,'access_token':'synthetic-access','refresh_token':'synthetic-refresh','account_id':'synthetic-account'},'last_refresh':'2026-09-01T00:00:00Z'}));auth.chmod(0o600)
  env={'PATH':'/usr/bin:/bin','HOME':root,'CODEX_HOME':root,'CODEX_REVOKE_TOKEN_URL_OVERRIDE':f'http://127.0.0.1:{server.server_port}/oauth/revoke'}
  p=subprocess.run([str(binary),'-c','cli_auth_credentials_store="file"','logout'],env=env,cwd=root,capture_output=True,timeout=25)
  reports.append({'provider_status':status,'exit':p.returncode,'local_auth_removed':not auth.exists(),'calls':calls})
 server.shutdown();server.server_close();thread.join()
print(json.dumps(reports,indent=2))
assert all(r['exit']==0 and r['local_auth_removed'] and r['calls']==[{'path':'/oauth/revoke','refresh_selected':True,'hint':'refresh_token'}] for r in reports)

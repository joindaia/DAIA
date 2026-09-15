"""Pinned native-client lifecycle on the trusted side, never inside the worker.

Requires an existing dedicated private profile. No browser login is initiated,
no consent renewed and no worker or model task started. Raw credentials remain
in this process/profile and are never printed. This is a probe, not an identity
attestation or a general credential API. Run as the profile owner.
"""
import hashlib,json,os,pathlib,selectors,subprocess,time
import argparse
parser=argparse.ArgumentParser(description='Trusted-side native Codex refresh/restart probe; existing dedicated login required. No model work.')
parser.add_argument('--binary',type=pathlib.Path,required=True)
parser.add_argument('--home',type=pathlib.Path,required=True)
args=parser.parse_args()
binary=args.binary
if not (not binary.is_symlink() and binary.is_file()):
 raise RuntimeError('Native client must be a regular unlinked file')
if not (hashlib.sha256(binary.read_bytes()).hexdigest()=='56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da'):
 raise RuntimeError('Native client digest mismatch')
home=args.home
if not (home.is_absolute() and not home.is_symlink() and home.is_dir()):
 raise RuntimeError('Dedicated authentication directory required')
auth=home/'auth.json'
if not (not auth.is_symlink() and auth.is_file()):
 raise RuntimeError('Regular authentication file required')
if not (home.stat().st_uid==os.getuid() and auth.stat().st_uid==os.getuid()):
 raise RuntimeError('Authentication profile owner mismatch')
if not (home.stat().st_mode & 0o077 == 0 and auth.stat().st_mode & 0o077 == 0):
 raise RuntimeError('Authentication profile must be private')
before=json.loads(auth.read_text())
results=[]
for force in (True,False):
 p=subprocess.Popen([str(binary),'app-server'],cwd='/tmp',env={'PATH':'/usr/bin:/bin','HOME':str(home),'CODEX_HOME':str(home)},stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 buf=b''
 def call(i,method,params):
  global buf
  received=0
  p.stdin.write(json.dumps({'id':i,'method':method,'params':params}).encode()+b'\n');p.stdin.flush()
  end=time.monotonic()+45
  with selectors.DefaultSelector() as s:
   s.register(p.stdout,selectors.EVENT_READ)
   while time.monotonic()<end:
    while b'\n' in buf:
     line,buf=buf.split(b'\n',1)
     msg=json.loads(line)
     if msg.get('id')==i:
      if 'error' in msg: raise RuntimeError('native RPC failed; payload withheld')
      return msg['result']
    if not s.select(max(0,end-time.monotonic())): break
    chunk=os.read(p.stdout.fileno(),65536)
    if not chunk: raise RuntimeError('native client stopped')
    received+=len(chunk)
    if received>1024*1024:raise RuntimeError('native response limit exceeded')
    buf+=chunk
  raise TimeoutError('native RPC timeout')
 try:
  call(1,'initialize',{'clientInfo':{'name':'daia-auth-lifecycle','version':'0.1'}})
  p.stdin.write(b'{"method":"initialized"}\n');p.stdin.flush()
  result=call(2,'account/read',{'refreshToken':force})
  results.append({'forced_refresh_requested':force,'chatgpt_account_returned':result.get('account',{}).get('type')=='chatgpt'})
 finally:
  p.stdin.close()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 after=json.loads(auth.read_text())
 results[-1].update({'exit_code':p.returncode,'access_token_changed':before['tokens']['access_token']!=after['tokens']['access_token'],'refresh_token_changed':before['tokens']['refresh_token']!=after['tokens']['refresh_token'],'account_unchanged':before['tokens']['account_id']==after['tokens']['account_id'],'auth_file_private':auth.stat().st_mode & 0o077 == 0})
 before=after
report={'native_version':'0.153.4','runs':results,'model_requests_requested':0,'raw_credentials_published':False,'worker_started':False}
if not (all(r['chatgpt_account_returned'] and r['account_unchanged'] and r['auth_file_private'] and r['exit_code']==0 for r in results)):
 raise RuntimeError('Native authentication lifecycle verification failed')
if not (results[0]['access_token_changed'] and results[0]['refresh_token_changed']):
 raise RuntimeError('Native credential refresh not established')
if not (not results[1]['access_token_changed'] and not results[1]['refresh_token_changed']):
 raise RuntimeError('Native restart unexpectedly changed credentials')
print(json.dumps(report))

# Guest-only public lab fixture. Never execute on the host.
import pathlib,subprocess,hashlib,json,os
pathlib.Path('/mnt/native').mkdir();subprocess.run(['mount','-o','ro','/dev/sr0','/mnt/native'],check=True)
b=pathlib.Path('/mnt/native/codex').read_bytes();assert hashlib.sha256(b).hexdigest()=='56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da'
pathlib.Path('/opt/codex').write_bytes(b);os.chmod('/opt/codex',0o755);bw=pathlib.Path('/mnt/native/bwrap').read_bytes();assert hashlib.sha256(bw).hexdigest()=='52231e1caf55bcbc667b269f49c63599a6f7db4767ae6a039580d0ff853db712';pathlib.Path('/usr/bin/bwrap').write_bytes(bw);os.chmod('/usr/bin/bwrap',0o755)
companion=pathlib.Path('/mnt/native/codex-code-mode-host');companion_present=companion.exists();companion_sha256=None
if companion_present:
 c=companion.read_bytes();companion_sha256=hashlib.sha256(c).hexdigest();assert companion_sha256=='3e85d67471825f73d02ff5f7e047ca1f6ca8caa3f59e4c6e8d9ca6ca7302cb45';pathlib.Path('/opt/codex-code-mode-host').write_bytes(c);os.chmod('/opt/codex-code-mode-host',0o755)
subprocess.run(['umount','/mnt/native'],check=True)
home=pathlib.Path('/home/worker');state=home/'.codex';state.mkdir(parents=True);(state/'config.toml').write_text('model = "gpt-5.3-codex-spark"\nmodel_provider = "daia_fixture"\napproval_policy = "never"\nweb_search = "disabled"\n[sandbox_workspace_write]\nnetwork_access = true\n[model_providers.daia_fixture]\nname = "DAIA fixture"\nbase_url = "http://10.0.2.101:3128/v1"\nwire_api = "responses"\nrequires_openai_auth = false\nrequest_max_retries = 0\nstream_max_retries = 0\nsupports_websockets = false\nstream_idle_timeout_ms = 90000\n')
pathlib.Path('/work').mkdir(exist_ok=True)
import socket,copy
base=json.loads(pathlib.Path('/opt/test-template.json').read_text())
def wire(body,extra=b'',route=b'POST /v1/responses HTTP/1.1'):
 raw=json.dumps(body).encode()
 return route+b'\r\nHost: 10.0.2.101:3128\r\nContent-Type: application/json\r\nContent-Length: '+str(len(raw)).encode()+b'\r\n'+extra+b'\r\n'+raw
cases=[wire(base,extra=x) for x in [b'Authorization: Bearer fake\r\n',b'Transfer-Encoding: chunked\r\n',b'Content-Length: 1\r\n',b'Upgrade: websocket\r\n']]
cases += [wire(base,route=b'POST /connectors HTTP/1.1'),wire(base,route=b'CONNECT example.org:443 HTTP/1.1')]
for key,value in [('tools',[{'type':'mcp','server_url':'https://example.org'}]),('previous_response_id','foreign'),('input',[{'type':'item_reference','id':'foreign'}]),('store',True)]:
 body=copy.deepcopy(base);body[key]=value;cases.append(wire(body))
for route in [b'OPTIONS /v1/responses HTTP/1.1',b'GET /v1/models HTTP/1.1',b'GET /.well-known/oauth-authorization-server HTTP/1.1',b'GET /mcp HTTP/1.1',b'POST /mcp HTTP/1.1',b'GET /openapi.json HTTP/1.1',b'GET /tools/list HTTP/1.1']:
 cases.append(wire(base,route=route))
for method in ['initialize','tools/list','resources/list','prompts/list','rpc.discover','unknown']:
 cases.append(wire({'jsonrpc':'2.0','id':1,'method':method,'params':{}}))
for raw in cases:
 with socket.create_connection(('10.0.2.101',3128),timeout=5) as s:
  s.sendall(raw);reply=s.recv(1024)
  assert reply.startswith(b'HTTP/1.1 403'),repr(reply[:50])
attack_count=len(cases)

import socket
research_denied=0
for target in ['127.0.0.1:443','169.254.169.254:443','100.64.0.1:443','[::1]:443','chatgpt.com:443','auth.openai.com:443']:
 with socket.create_connection(('10.0.2.102',3128),timeout=5) as sock:
  sock.sendall(('CONNECT '+target+' HTTP/1.1\r\nHost: '+target+'\r\n\r\n').encode())
  assert sock.recv(100).startswith(b'HTTP/1.1 403')
  research_denied+=1

env={'HOME':str(home),'CODEX_HOME':str(state),'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'}
pathlib.Path('/work/version_check.py').write_text('def newer(a, b): return a > b\n')
pathlib.Path('/work/test_version.py').write_text('from version_check import newer\nfor a,b,want in [("1.10","1.9",True),("1","1.0",False),("1.0.1","1",True),("1.2","1.10",False)]:\n    assert newer(a,b)==want, (a,b,want)\nprint("4 tests passed")\n')
r=subprocess.run(['/opt/codex','--strict-config','exec','--skip-git-repo-check','--ephemeral','--sandbox','workspace-write','--json','-C','/work','First run python3 /work/research.py to fetch public Python documentation and verify a downloaded packaging dependency. Read a short relevant excerpt from /work/research/stdtypes.html about comparisons. Then fix /work/version_check.py using only the standard library, retaining no dependency requirement in the final source. Keep exploration to the two supplied files: read version_check.py and test_version.py together in one command, then edit and run the test. Use at most three terminal calls if possible. Inputs are dot-separated nonnegative integer release components. Compare numerically and treat trailing zero components as equal. Use ls and cat (ripgrep is not installed) to inspect the files, edit version_check.py and run python3 test_version.py. Do not change the test file. Finish with a short report.'],env=env,capture_output=True,text=True,timeout=100)
events=[json.loads(line) for line in r.stdout.splitlines() if line.startswith('{')]
items=[e['item'] for e in events if e.get('type')=='item.completed']
src=pathlib.Path('/work/version_check.py').read_text();assert len(src.encode())<=8192
result={'attacks_denied':attack_count,'nonce':'83344227ed564314a89e1589699e29d9','companion_present':companion_present,'companion_sha256':companion_sha256,'native_exit':r.returncode,'turn_completed':any(e.get('type')=='turn.completed' for e in events),'synthetic_model':False,'source':src,'item_types':[i.get('type') for i in items],'commands':[{'command':i.get('command'),'exit_code':i.get('exit_code')} for i in items if i.get('type')=='command_execution'],'test_unchanged':pathlib.Path('/work/test_version.py').read_text()=='from version_check import newer\nfor a,b,want in [("1.10","1.9",True),("1","1.0",False),("1.0.1","1",True),("1.2","1.10",False)]:\n    assert newer(a,b)==want, (a,b,want)\nprint("4 tests passed")\n'}
root=pathlib.Path('/work/research')
research_diagnostic={'stage':'research_result','native_exit':r.returncode,'files':{name:(root/name).is_file() for name in ('stdtypes.html','packaging-25.0-py3-none-any.whl','result.json','failure.json')}}
failure=root/'failure.json'
if failure.is_file() and failure.stat().st_size<=512:
 try:research_diagnostic['research_failure']=json.loads(failure.read_text())
 except (OSError,ValueError):pass
if result['native_exit']!=0 or not result['turn_completed']:
 with open('/dev/ttyS0','w') as out:out.write('\nDAIA_NATIVE_FAILURE '+json.dumps(research_diagnostic)+'\n')
 diagnostic={'native_exit':r.returncode,'turn_completed':result['turn_completed'],'event_types':[e.get('type') for e in events],'errors':[e.get('message',e.get('error',{})) for e in events if e.get('type') in ('error','turn.failed')],'stderr_tail':r.stderr[-3000:]}
 with open('/dev/ttyS0','w') as out:out.write('DAIA_NATIVE_FAILURE '+json.dumps(diagnostic)+'\n')
 raise RuntimeError('native development failed; guest diagnostic recorded')
model_result=dict(result,research_negative_requests_denied=research_denied)
try:
 model_result['research']=json.loads(pathlib.Path('/work/research/result.json').read_text())
except (OSError,ValueError):
 with open('/dev/ttyS0','w') as out:out.write('\nDAIA_NATIVE_FAILURE '+json.dumps(research_diagnostic)+'\n')
 raise

s=socket.create_connection(('10.0.2.100',3128),timeout=8)
stream=s.makefile('rwb',buffering=0)
def send(value):stream.write(json.dumps(value).encode()+b'\n')
def rpc(i,method,params):
 send({'jsonrpc':'2.0','id':i,'method':method,'params':params})
 while True:
  line=stream.readline(65537)
  assert len(line)<=65536 and line.endswith(b'\n')
  value=json.loads(line)
  if value.get('id')==i:
   assert 'error' not in value
   return value['result']
rpc(1,'initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'DAIA-KVM-fixture','version':'1'}})
send({'jsonrpc':'2.0','method':'notifications/initialized'})
assert {t['name'] for t in rpc(2,'tools/list',{})['tools']}=={'heartbeat','submit_result'}
for i,name in enumerate(['request_work','stop_contributing','register_agent'],3):
 assert rpc(i,'tools/call',{'name':name,'arguments':{}})['isError']
assert rpc(50,'tools/call',{'name':'responses','arguments':{}})['isError']
assert not rpc(6,'tools/call',{'name':'heartbeat','arguments':{}}).get('isError',False)
packet={'source_digest': '56f13c1255799e0147d980ab82390e9792a9a7ce76f89b777ef552f4473f9c5f', 'line': 1, 'finding': 'String comparison misorders numeric release components.', 'reproduction_outline': 'The supplied original fixture fails numerical version tests; the native client ran the unchanged test file. Independent evaluation remains separate.', 'suggested_change': 'placeholder'}
packet['suggested_change']=model_result['source']
args={'artifact':json.dumps(packet),'verdict':'candidate'}
assert rpc(7,'tools/call',{'name':'submit_result','arguments':args})['isError']
wrong={**args,'artifact':args['artifact']+' '}
assert rpc(8,'tools/call',{'name':'submit_result','arguments':wrong})['isError']
receipt=rpc(9,'tools/call',{'name':'submit_result','arguments':args})
assert not receipt.get('isError',False)
data=receipt.get('structuredContent') or json.loads(receipt['content'][0]['text'])
assert data['status']=='already_recorded'
stream.close();s.close()

model_result.update(scoped_tools=True,wrong_retry_denied=True,exact_retry=True,receipt_hash=data['receipt_hash'])
with open('/dev/ttyS0','w') as out:out.write('\nDAIA_BOOT_RESULT '+json.dumps(model_result)+'\n')

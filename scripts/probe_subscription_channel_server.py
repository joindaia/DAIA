"""Test-only live subscription server for the private supervised KVM lab.

Uses the repository AssignmentModelChannel with a fixed CodexHTTPSUpstream.
The trusted launcher supplies the approved template and outside-guest credentials;
only that launcher may service the native refresh handoff. No guest API exposes
credential replacement. This is not a standalone production login broker or
participant installer. Run only with the documented isolated service/watchdog.
"""
import sys,types,json,os,socket,pathlib,http.client,time
from pathlib import Path
package=types.ModuleType('daia');package.__path__=['/var/lib/daia-lab/templates'];sys.modules['daia']=package
from daia.model_request import RequestGate, _decode, Denied, _history
from daia.model_channel import AssignmentModelChannel
from daia.codex_https import CodexHTTPSUpstream
from daia.model_response import completed_output
root=Path('/run/daia-lab')
template=json.loads(Path('/var/lib/daia-lab/templates/model-template.json').read_text());template['model']='gpt-5.3-codex-spark'
credentials=json.loads((root/'subscription-auth.json').read_text());(root/'subscription-auth.json').unlink()
binding=CodexHTTPSUpstream(credentials['address'],credentials['access_token'],credentials['account_id'],seconds=150,requests=6)
credentials.clear();counts={'forwarded':0,'denied':0,'attempts':0,'statuses':[]}
original_getresponse=http.client.HTTPConnection.getresponse
def observed_response(connection):
 response=original_getresponse(connection)
 counts['last_provider_status']=response.status
 return response
http.client.HTTPConnection.getresponse=observed_response

def forward(raw):
 counts['attempts']+=1
 if counts['forwarded']==1 and not counts.get('credential_rotated'):
  deadline=binding._deadline
  print('DAIA_ROTATION_REQUESTED',flush=True)
  (root/'rotation-request').touch(mode=0o600)
  end=time.monotonic()+40
  replacement=root/'rotation-credential.json'
  while not replacement.exists() and time.monotonic()<end:time.sleep(.05)
  if not replacement.exists():binding.revoke();raise Denied('trusted refresh unavailable')
  updated=json.loads(replacement.read_text());replacement.unlink()
  binding.replace_credential(updated['access_token']);updated.clear()
  assert binding._deadline==deadline
  counts['credential_rotated']=True
  print('DAIA_ROTATION_APPLIED',flush=True)
  counts['deadline_preserved']=True
 try:
  out=binding(raw)
 except Denied as error:
  counts['upstream_failure']=str(error)
  raise
 counts['forwarded']+=1
 if counts['forwarded']==1 and (root/'crash-before-first-response').exists():
  # Test-only trusted controller rendezvous. Never requested by a worker.
  (root/'crash-ready').touch(mode=0o600)
  end=time.monotonic()+15
  while (root/'crash-before-first-response').exists() and time.monotonic()<end:time.sleep(.02)
  if (root/'crash-before-first-response').exists():
   binding.revoke();raise Denied('crash controller did not acknowledge')
 return out
channel=AssignmentModelChannel(json.dumps(template).encode(),forward,authority='10.0.2.101:3128')
try:
 with socket.socket(socket.AF_UNIX) as listener:
  listener.bind(str(root/'model.sock'));os.chmod(root/'model.sock',0o660);listener.listen(4)
  while True:
   conn,_=listener.accept();ok=channel.serve(conn)
   counts['denied']+=int(not ok);(root/'subscription-audit.json').write_text(json.dumps(counts))
finally:binding.revoke()

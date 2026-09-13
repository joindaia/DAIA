"""Root lab integration test; synthetic identity only, no model credentials."""
from pathlib import Path
import asyncio,json,os,pwd,subprocess,sys,tempfile
import argparse
parser=argparse.ArgumentParser(description='Synthetic pending-receipt service probe on the configured lab host.')
parser.add_argument('--python-runtime',type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1];sys.path[:0]=[str(repo/'src'),str(repo/'tests')]
from daia.service import Coordinator
from daia.store import Store
from daia.contributor import Contributor
from daia.mcp_server import build_mcp_app
from test_contributor import direct,invite_file
from test_assignment_host import approve
from test_mcp import running_server
owner=pwd.getpwnam('daia-controller')
with tempfile.TemporaryDirectory(prefix='daia-receipt-runner-') as directory:
 base=Path(directory);base.chmod(0o755);state=base/'state';state.mkdir(mode=0o700)
 service=Coordinator(Store(str(base/'coordinator.sqlite3')));service.seed()
 with running_server(build_mcp_app(service)) as url:
  invite=invite_file(state,service,url,max_jobs=1);host=direct(Contributor(invite,max_jobs=1),service)
  async def prepare():
   assignment=await host.perform('request_work');authority=approve(host,assignment,['read_input','heartbeat','submit_result']);host.job_authority=authority;direct(host,service,lose='submit_result')
   try:await host.perform('submit_result',assignment_id=assignment['assignment_id'],artifact='{"factors":[101,103]}',verdict='candidate')
   except ValueError as e:assert 'response loss' in str(e)
   else:raise AssertionError('Loss not injected')
   return assignment['assignment_id'],authority
  assignment,authority=asyncio.run(prepare());auth=base/'authority.json';auth.write_text(json.dumps(authority));auth.chmod(0o600);os.chown(auth,owner.pw_uid,owner.pw_gid)
  os.chown(state,owner.pw_uid,owner.pw_gid)
  for p in state.iterdir():os.chown(p,owner.pw_uid,owner.pw_gid);p.chmod(0o600)
  before=json.loads(host.path.read_text());assert before['pending']
  def forbidden(*a,**kw):raise AssertionError('New work forbidden')
  service.request_work=forbidden
  cmd=['/usr/bin/python3',str(repo/'scripts/run_pending_receipt_lab.py'),'--invite',str(invite),'--authority',str(auth),'--assignment',assignment,'--python-runtime',str(args.python_runtime)]
  run=subprocess.run(cmd,capture_output=True,timeout=40);assert run.returncode==0,run.stdout.decode()
  after=json.loads(host.path.read_text());assert after['pending'] is None and after['receipt']['status']=='already_recorded'
  assert {k:after[k] for k in ['key','used','deadline','max_jobs']}=={k:before[k] for k in ['key','used','deadline','max_jobs']}
  saved=host.path.read_bytes();again=subprocess.run(cmd,capture_output=True,timeout=40)
  assert again.returncode==1 and host.path.read_bytes()==saved and service.metrics()['results']==1
  report={'repository_entrypoint_success':True,'synthetic_submission':True,'repeat_refused':True,'state_unchanged_on_repeat':True,'results':1,'identity_and_consent_unchanged':True,'model_requests':0}
  print(json.dumps(report))

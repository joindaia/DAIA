"""Test-only subscription lab service; requires the controller isolation profile."""
if not __debug__:
    raise SystemExit("Optimized Python is unsupported for lab execution")

import sys,json,asyncio,os,pathlib
assert os.geteuid()!=0
assert not pathlib.Path("/mnt/c").exists()
pathlib.Path("/state/runtime-check.json").write_text(json.dumps({"nonroot":True,"personal_mount_absent":True}))
from daia.contributor import Contributor,build_assignment_server
c=json.load(open(sys.argv[1]));host=Contributor(c['invite'],job_authority=c['authority']);remote=host.remote;lost=False;delivery_audit=[]
async def wrapped(name,**args):
 global lost
 result=await remote(name,**args)
 if name in ('heartbeat','submit_result'):
  delivery_audit.append({'operation':name,'status':result.get('status')})
  if name=='submit_result' and not lost:delivery_audit[-1]['receipt_hidden']=True
  pathlib.Path('/state/delivery-audit.json').write_text(json.dumps(delivery_audit))
 if name=='submit_result' and not lost:
  lost=True
  raise ValueError('Synthetic response loss after committed submission')
 return result
host.remote=wrapped
asyncio.run(build_assignment_server(host,c['assignment'],retry_receipt=c.get('retry_receipt',False)).run_stdio_async())

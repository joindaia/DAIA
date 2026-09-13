"""Test-only subscription lab service; requires the controller isolation profile."""
import sys,json,asyncio,os,pathlib
assert os.geteuid()!=0
assert not pathlib.Path("/mnt/c").exists()
pathlib.Path("/state/runtime-check.json").write_text(json.dumps({"nonroot":True,"personal_mount_absent":True}))
from daia.contributor import Contributor,build_assignment_server
c=json.load(open(sys.argv[1]));host=Contributor(c['invite'],job_authority=c['authority']);remote=host.remote;lost=False
async def wrapped(name,**args):
 global lost
 result=await remote(name,**args)
 if name=='submit_result' and not lost:
  lost=True
  raise ValueError('Synthetic response loss after committed submission')
 return result
host.remote=wrapped
asyncio.run(build_assignment_server(host,c['assignment']).run_stdio_async())

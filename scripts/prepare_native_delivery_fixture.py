"""Lab-only native MCP variant of the approved research fixture. Trusted inputs only.

No login, provider request or candidate execution occurs during preparation.
The existing source fixture, native binaries and ISO builder are operator supplied.
"""
from pathlib import Path
import json,uuid,hashlib,subprocess
import argparse
parser=argparse.ArgumentParser(description='Prepare the lab-only native MCP delivery fixture; no login or execution.')
for name in ('source','output','native-directory','iso-builder'):
 parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1];old=args.source;out=args.output
out.mkdir()  # Never overwrite an existing approved fixture.

data=json.loads((old/'user-data').read_text().split('\n',1)[1]);entry=next(x for x in data['write_files'] if x['path']=='/tmp/probe.py');code=entry['content'];nonce=uuid.uuid4().hex
old_nonce=json.loads((old/'config.json').read_text())['nonce']
if code.count(old_nonce)!=1:raise ValueError('Unexpected source nonce binding')
code=code.replace(old_nonce,nonce)
marker="pathlib.Path('/work').mkdir(exist_ok=True)"
config='\n[mcp_servers.daia_assignment]\ncommand = "/usr/bin/python3"\nargs = ["/opt/assignment-stdio.py"]\nstartup_timeout_sec = 10\ntool_timeout_sec = 10\n[mcp_servers.daia_assignment.tools.heartbeat]\napproval_mode = "approve"\n[mcp_servers.daia_assignment.tools.submit_result]\napproval_mode = "approve"\n'
code=code.replace(marker,marker+"\nwith (state/'config.toml').open('a') as f:f.write("+repr(config)+")")
a=code.index("'First run python3 /work/research.py");b=code.index("'],env=",a)
packet={'source_digest':'56f13c1255799e0147d980ab82390e9792a9a7ce76f89b777ef552f4473f9c5f','line':1,'finding':'String comparison misorders numeric release components.','reproduction_outline':'The original fixture fails numerical version comparison tests. The unchanged supplied test must pass after the patch.','suggested_change':'REPLACE WITH THE EXACT COMPLETE CONTENT OF version_check.py'}
prompt = """Complete this assigned development task using native DAIA MCP tools. Call heartbeat once. Then use EXACTLY ONE terminal invocation to: run python3 /work/research.py; show a short comparison excerpt from /work/research/stdtypes.html; read the two supplied files; overwrite only version_check.py with your fix; run python3 test_version.py; print the complete resulting source. The original source is `def newer(a, b): return a > b`. Inputs are dot-separated nonnegative integer components. Compare numerically and ignore trailing zero components. Use only the standard library in the final source. The tests check 1.10 > 1.9, 1 == 1.0, 1.0.1 > 1 and 1.2 < 1.10. Do not change tests. You can design the fix now because the entire original implementation and requirements are supplied. Do not spend extra terminal calls on exploration. Then call submit_result with verdict candidate and artifact equal to a JSON string of this packet, replacing suggested_change with the exact complete source: """ + json.dumps(packet) + """ . The first submit response is intentionally lost AFTER persistence. Retry submit_result once with EXACTLY the identical artifact string and verdict, even if the tool only reports a generic error. Do not change whitespace or call heartbeat again. Finish after the retry receipt. Maximum six model requests; target one heartbeat, ONE terminal call, two submit calls, then final confirmation. Do not invoke MCP through shell."""

code=code[:a]+repr(prompt)+code[b+1:]
a=code.index("s=socket.create_connection(('10.0.2.100',3128),timeout=8)")
code=code[:a]+"""mcp_items=[i for i in items if i.get('type')=='mcp_tool_call']
assert len(mcp_items)>=3,'Native MCP calls absent'
model_result.update(native_mcp_delivery=True,native_mcp_items=len(mcp_items))
with open('/dev/ttyS0','w') as out:out.write('\\nDAIA_BOOT_RESULT '+json.dumps(model_result)+'\\n')
"""
compile(code,'native-delivery-probe','exec');entry['content']=code
for filename in ['__init__.py','assignment_guest.py','assignment_relay.py']:
 data['write_files'].append({'path':'/opt/daia/'+filename,'content':(repo/'src/daia'/filename).read_text(),'permissions':'0444'})
data['write_files'].append({'path':'/opt/assignment-stdio.py','content':'from daia.assignment_guest import main\nraise SystemExit(main())\n','permissions':'0444'})
(out/'user-data').write_text('#cloud-config\n'+json.dumps(data));(out/'meta-data').write_text(json.dumps({'instance-id':'daia-native-'+nonce,'local-hostname':'daia-native'}));(out/'network-config').write_bytes((old/'network-config').read_bytes())
subprocess.run([str(args.iso_builder),'-quiet','-output',str(out/'seed.iso'),'-volid','CIDATA','-joliet','-rock',str(out/'user-data'),str(out/'meta-data'),str(out/'network-config'),str(args.native_directory/'codex'),str(args.native_directory/'bwrap')],check=True)
cfg=json.loads((old/'config.json').read_text());cfg.update(nonce=nonce,seed_sha256=hashlib.sha256((out/'seed.iso').read_bytes()).hexdigest());(out/'config.json').write_text(json.dumps(cfg));(out/'probe.py').write_bytes((old/'probe.py').read_bytes())
print('Prepared native MCP guest; no provider request made.')

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
COMPANION_PIN='3e85d67471825f73d02ff5f7e047ca1f6ca8caa3f59e4c6e8d9ca6ca7302cb45'
def companion_inputs(native):
 native=Path(native); paths=[native/'codex',native/'bwrap']; companion=native/'codex-code-mode-host'; present=companion.exists() or companion.is_symlink(); digest=None
 if present:
  if companion.is_symlink() or not companion.is_file(): raise ValueError('Pinned companion regular file required')
  with companion.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
  if digest!=COMPANION_PIN: raise ValueError('Native companion pin mismatch')
  paths.append(companion)
 return paths,present,digest
def validate_source_companion(source_config, present, digest):
 expected_present=source_config.get('companion_present',False)
 expected_digest=source_config.get('companion_sha256')
 if type(expected_present) is not bool or expected_present != present or expected_digest != (COMPANION_PIN if present else None):
  raise ValueError('Derived fixture companion metadata mismatch')
repo=Path(__file__).resolve().parents[1];old=args.source;out=args.output
native_inputs,companion_present,companion_sha256=companion_inputs(args.native_directory)
source_config=json.loads((old/'config.json').read_text())
validate_source_companion(source_config,companion_present,companion_sha256)
out.mkdir()  # Never overwrite an existing approved fixture.

data=json.loads((old/'user-data').read_text().split('\n',1)[1]);entry=next(x for x in data['write_files'] if x['path']=='/tmp/probe.py');code=entry['content'];nonce=uuid.uuid4().hex
old_nonce=source_config['nonce']
if code.count(old_nonce)!=1:raise ValueError('Unexpected source nonce binding')
code=code.replace(old_nonce,nonce)
marker="pathlib.Path('/work').mkdir(exist_ok=True)"
config='\n[mcp_servers.daia_assignment]\ncommand = "/usr/bin/python3"\nargs = ["/opt/assignment-stdio.py"]\nstartup_timeout_sec = 10\ntool_timeout_sec = 10\n[mcp_servers.daia_assignment.tools.heartbeat]\napproval_mode = "approve"\n[mcp_servers.daia_assignment.tools.submit_result]\napproval_mode = "approve"\n'
native_source = "Complete this assigned development task using native DAIA MCP tools." in code
if not native_source: code=code.replace(marker,marker+"\nwith (state/'config.toml').open('a') as f:f.write("+repr(config)+")")
prompt_marker = "'Complete this assigned development task" if native_source else "'First run python3 /work/research.py"
a=code.index(prompt_marker);b=code.index("'],env=",a)
packet={'source_digest':'56f13c1255799e0147d980ab82390e9792a9a7ce76f89b777ef552f4473f9c5f','line':1,'finding':'String comparison misorders numeric release components.','reproduction_outline':'The original fixture fails numerical version comparison tests. The unchanged supplied test must pass after the patch.','suggested_change':'REPLACE WITH THE EXACT COMPLETE CONTENT OF version_check.py'}
prompt = """Complete this assigned development task using native DAIA MCP tools. Call heartbeat once. Then use EXACTLY ONE terminal invocation to: run python3 /work/research.py; show a short comparison excerpt from /work/research/stdtypes.html; read the two supplied files; overwrite only version_check.py with your fix; run python3 test_version.py; print the complete resulting source. The original source is `def newer(a, b): return a > b`. Inputs are dot-separated nonnegative integer components. Compare numerically and ignore trailing zero components. Use only the standard library in the final source. The tests check 1.10 > 1.9, 1 == 1.0, 1.0.1 > 1 and 1.2 < 1.10. Do not change tests. You can design the fix now because the entire original implementation and requirements are supplied. Do not spend extra terminal calls on exploration. Then call submit_result with verdict candidate and artifact equal to a JSON string of this packet, replacing suggested_change with the exact complete source: """ + json.dumps(packet) + """ . The trusted helper recovers one intentionally lost receipt using the exact saved submission. Call submit_result once and finish after its confirmed receipt. Do not call heartbeat again. Maximum six model requests; target one heartbeat, ONE terminal call, one submit call, then final confirmation. Do not invoke MCP through shell."""

code=code[:a]+repr(prompt)+code[b+1:]
a=code.index("mcp_items=" if native_source else "s=socket.create_connection(('10.0.2.100',3128),timeout=8)")
code=code[:a]+"""mcp_items=[i for i in items if i.get('type')=='mcp_tool_call']
assert len(mcp_items)>=2,'Native MCP calls absent'
model_result.update(native_mcp_delivery=True,native_mcp_items=len(mcp_items))
with open('/dev/ttyS0','w') as out:out.write('\\nDAIA_BOOT_RESULT '+json.dumps(model_result)+'\\n')
"""
compile(code,'native-delivery-probe','exec');entry['content']=code
data['write_files']=[x for x in data['write_files'] if x['path'] not in ('/opt/daia/__init__.py','/opt/daia/assignment_guest.py','/opt/daia/assignment_relay.py','/opt/assignment-stdio.py')]
for filename in ['__init__.py','assignment_guest.py','assignment_relay.py']:
 data['write_files'].append({'path':'/opt/daia/'+filename,'content':(repo/'src/daia'/filename).read_text(),'permissions':'0444'})
data['write_files'].append({'path':'/opt/assignment-stdio.py','content':'from daia.assignment_guest import main\nraise SystemExit(main())\n','permissions':'0444'})
(out/'user-data').write_text('#cloud-config\n'+json.dumps(data));(out/'meta-data').write_text(json.dumps({'instance-id':'daia-native-'+nonce,'local-hostname':'daia-native'}));(out/'network-config').write_bytes((old/'network-config').read_bytes())
subprocess.run([str(args.iso_builder),'-quiet','-output',str(out/'seed.iso'),'-volid','CIDATA','-joliet','-rock',str(out/'user-data'),str(out/'meta-data'),str(out/'network-config'),*[str(path) for path in native_inputs]],check=True)
cfg=source_config;cfg.update(retry_receipt=True,nonce=nonce,companion_present=companion_present,companion_sha256=companion_sha256,seed_sha256=hashlib.sha256((out/'seed.iso').read_bytes()).hexdigest());(out/'config.json').write_text(json.dumps(cfg));(out/'probe.py').write_bytes((old/'probe.py').read_bytes())
print('Prepared native MCP guest; no provider request made.')

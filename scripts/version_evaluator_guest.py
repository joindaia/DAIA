"""Guest-only numeric-version fixture evaluator; embed in a disposable VM seed.

Never execute this script on the host. The trusted builder replaces NONCE.
Candidate code is untrusted and runs only inside the isolated evaluator guest.
"""
import pathlib,json,hashlib,subprocess,pwd
p=pathlib.Path('/tmp/candidate.json');patch=json.loads(p.read_text())
assert isinstance(patch,str) and len(patch.encode())<8192
new=patch
old='def newer(a, b): return a > b\n'
root=pathlib.Path('/tmp/evaluate');root.mkdir();(root/'candidate.py').write_text(new);(root/'original.py').write_text(old)
cases=[('1.10','1.9',True),('1','1.0',False),('1.0.0','1',False),('1.0.1','1',True),('0.0','0',False),('2','1.999',True),('1.01','1.1',False),('1.2','1.10',False),('999999999999999999999','9',True),('1.2.3','1.2',True)]
# The privileged guest parent decides pass/fail. Candidate code never runs in
# that process and cannot write the checker, source or serial report endpoint.
serial=pathlib.Path('/dev/ttyS0');serial.chmod(0o600)
worker=pwd.getpwnam('nobody')
if worker.pw_uid==0:raise RuntimeError('Unprivileged evaluator identity required')
root.chmod(0o755)
runner=root/'invoke.py'
runner.write_text("import json,sys\nfrom importlib import import_module\nf=import_module(sys.argv[1]).newer\na,b=json.loads(sys.argv[2])\nprint(json.dumps(f(a,b)))\n")
for file in root.iterdir():file.chmod(0o644)
original_failed=False
for mod in ['candidate','original']:
 for a,b,expected in cases:
  r=subprocess.run(['python3','-B',str(runner),mod,json.dumps([a,b])],
      cwd=root,capture_output=True,timeout=5,user=worker.pw_uid,
      group=worker.pw_gid,extra_groups=[],env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent'})
  try:actual=json.loads(r.stdout) if r.returncode==0 else None
  except (ValueError,UnicodeError):actual=None
  passed=type(actual) is bool and actual is expected
  if mod=='candidate' and not passed:raise RuntimeError('Candidate result mismatch')
  if mod=='original' and not passed:original_failed=True
if not original_failed:raise RuntimeError('Original fixture unexpectedly passed')
result={'nonce':NONCE,'cases_passed':len(cases),'original_failed':True,'source_sha256':hashlib.sha256(new.encode()).hexdigest(),'proposal_sha256':hashlib.sha256(patch.encode()).hexdigest(),'format_normalized':False,'model_source_changed':False,'provider_credentials_present':False,'candidate_separate_uid':True,'parent_compares_results':True}
with open('/dev/ttyS0','w') as out:out.write('\nDAIA_BOOT_RESULT '+json.dumps(result)+'\n')

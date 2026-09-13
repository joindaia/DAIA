"""Guest-only numeric-version fixture evaluator; embed in a disposable VM seed.

Never execute this script on the host. The trusted builder replaces NONCE.
Candidate code is untrusted and runs only inside the isolated evaluator guest.
"""
import pathlib,json,hashlib,subprocess
p=pathlib.Path('/tmp/candidate.json');patch=json.loads(p.read_text())
assert isinstance(patch,str) and len(patch.encode())<8192
new=patch
old='def newer(a, b): return a > b\n'
root=pathlib.Path('/tmp/evaluate');root.mkdir();(root/'candidate.py').write_text(new);(root/'original.py').write_text(old)
cases=[('1.10','1.9',True),('1','1.0',False),('1.0.0','1',False),('1.0.1','1',True),('0.0','0',False),('2','1.999',True),('1.01','1.1',False),('1.2','1.10',False),('999999999999999999999','9',True),('1.2.3','1.2',True)]
test='import sys\nfrom '+ 'MODULE' +' import newer\ncases='+repr(cases)+'\nassert all(newer(a,b) is expected for a,b,expected in cases)\n'
for mod in ['candidate','original']:
 (root/'check.py').write_text(test.replace('MODULE',mod))
 r=subprocess.run(['python3','check.py'],cwd=root,capture_output=True,timeout=5)
 if mod=='candidate':assert r.returncode==0
 else:assert r.returncode!=0
result={'nonce':NONCE,'cases_passed':len(cases),'original_failed':True,'source_sha256':hashlib.sha256(new.encode()).hexdigest(),'proposal_sha256':hashlib.sha256(patch.encode()).hexdigest(),'format_normalized':False,'model_source_changed':False,'provider_credentials_present':False}
with open('/dev/ttyS0','w') as out:out.write('\nDAIA_BOOT_RESULT '+json.dumps(result)+'\n')

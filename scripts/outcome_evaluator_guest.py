"""Guest-only outcome-summary task evaluator; embed in a disposable VM seed.

Never execute this script on the host. The trusted builder replaces NONCE.
Candidate code is untrusted and runs only inside the isolated evaluator guest.
"""
import pathlib,json,hashlib,subprocess,pwd
p=pathlib.Path('/tmp/candidate.json');patch=json.loads(p.read_text())
assert isinstance(patch,str) and len(patch.encode())<8192
old='"""Private lab outcome export; no retry, signing, admission or model authority."""\nimport json\nimport os\nfrom pathlib import Path\nimport re\nimport tempfile\n\n\ndef outcome(saved, assignment):\n    result = {\'worker_completed\': False, \'delivery\': \'unconfirmed\',\n              \'automatic_retry_authorized\': False}\n    if not assignment or assignment.get(\'state\') != \'submitted\':\n        return result\n    expected = assignment.get(\'receipt_hash\')\n    if not isinstance(expected, str) or not re.fullmatch(\'[0-9a-f]{64}\', expected):\n        return result\n    receipt = saved.get(\'receipt\')\n    if (saved.get(\'pending\') is None and saved.get(\'lease\') is None\n            and isinstance(receipt, dict) and receipt.get(\'receipt_hash\') == expected):\n        result.update(delivery=\'acknowledged\', receipt_hash=expected)\n    elif (isinstance(saved.get(\'pending\'), dict)\n          and saved[\'pending\'].get(\'assignment_id\') == assignment.get(\'id\')\n          and saved.get(\'pending_receipt_hash\') == expected):\n        result.update(delivery=\'stored_unacknowledged\', receipt_hash=expected)\n    return result\n\n\ndef write_outcome(path, data):\n    path = Path(path)\n    fd, temporary = tempfile.mkstemp(prefix=\'.daia-outcome-\', dir=path.parent)\n    try:\n        with os.fdopen(fd, \'w\') as stream:\n            json.dump(data, stream)\n            stream.flush(); os.fsync(stream.fileno())\n        os.replace(temporary, path)\n        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)\n        try: os.fsync(parent)\n        finally: os.close(parent)\n    finally:\n        Path(temporary).unlink(missing_ok=True)\n\n\ndef new_run_directory(root):\n    """Allocate isolated persistent lab state; never reuse or migrate a run."""\n    root = Path(root)\n    root.mkdir(mode=0o700, exist_ok=True)\n    info = root.lstat()\n    if root.is_symlink() or not root.is_dir() or info.st_uid != os.geteuid() or info.st_mode & 0o077:\n        raise ValueError(\'Private operator-owned state root required\')\n    run = Path(tempfile.mkdtemp(prefix=\'run-\', dir=root))\n    for name in (\'assignment\', \'coordinator\'):\n        (run / name).mkdir(mode=0o700)\n    for directory in (run, root):\n        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)\n        try: os.fsync(fd)\n        finally: os.close(fd)\n    return run\n'
new=old+'\n'+patch
import ast
addition=ast.parse(patch).body
if len(patch)>1200 or len(addition)!=1 or not isinstance(addition[0],ast.FunctionDef) or addition[0].name!='summarize_outcomes':raise RuntimeError('Expected one bounded appended function')
original_functions={n.name:ast.dump(n) for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)}
updated_functions={n.name:ast.dump(n) for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
if any(updated_functions.get(k)!=v for k,v in original_functions.items()):raise RuntimeError('Existing function modified')
root=pathlib.Path('/tmp/evaluate');root.mkdir();(root/'candidate.py').write_text(new);(root/'original.py').write_text(old)
cases=[([], None, {'total': 0, 'worker_completed': 0, 'acknowledged': 0, 'stored_unacknowledged': 0, 'unconfirmed': 0}), ([{}], None, {'total': 1, 'worker_completed': 0, 'acknowledged': 0, 'stored_unacknowledged': 0, 'unconfirmed': 1}), ([{'delivery': 'acknowledged', 'worker_completed': False}], None, {'total': 1, 'worker_completed': 0, 'acknowledged': 1, 'stored_unacknowledged': 0, 'unconfirmed': 0}), ([{'delivery': 'stored_unacknowledged', 'worker_completed': True}], None, {'total': 1, 'worker_completed': 1, 'acknowledged': 0, 'stored_unacknowledged': 1, 'unconfirmed': 0}), ([{'delivery': 'unconfirmed', 'worker_completed': 1}], None, {'total': 1, 'worker_completed': 0, 'acknowledged': 0, 'stored_unacknowledged': 0, 'unconfirmed': 1}), ([{'delivery': None, 'worker_completed': True, 'secret': 'synthetic'}], None, {'total': 1, 'worker_completed': 1, 'acknowledged': 0, 'stored_unacknowledged': 0, 'unconfirmed': 1}), ([{'delivery': 'unknown'}, {'delivery': 'acknowledged', 'worker_completed': True}, {'delivery': 'stored_unacknowledged'}], None, {'total': 3, 'worker_completed': 1, 'acknowledged': 1, 'stored_unacknowledged': 1, 'unconfirmed': 1})]
# The privileged guest parent decides pass/fail. Candidate code never runs in
# that process and cannot write the checker, source or serial report endpoint.
serial=pathlib.Path('/dev/ttyS0');serial.chmod(0o600)
worker=pwd.getpwnam('nobody')
if worker.pw_uid==0:raise RuntimeError('Unprivileged evaluator identity required')
root.chmod(0o755)
runner=root/'invoke.py'
runner.write_text("import json,sys\nfrom importlib import import_module\nf=import_module(sys.argv[1]).summarize_outcomes\na,b=json.loads(sys.argv[2])\nbefore=json.dumps(a,sort_keys=True)\nresult=f(iter(a))\nif json.dumps(a,sort_keys=True)!=before:raise RuntimeError('Input mutated')\nprint(json.dumps(result))\n")
for file in root.iterdir():file.chmod(0o644)
original_failed=False
for mod in ['candidate','original']:
 for a,b,expected in cases:
  r=subprocess.run(['python3','-B',str(runner),mod,json.dumps([a,b])],
      cwd=root,capture_output=True,timeout=5,user=worker.pw_uid,
      group=worker.pw_gid,extra_groups=[],env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent'})
  try:actual=json.loads(r.stdout) if r.returncode==0 else None
  except (ValueError,UnicodeError):actual=None
  passed=type(actual) is dict and actual == expected and all(type(v) is int for v in actual.values())
  if mod=='candidate' and not passed:raise RuntimeError('Candidate result mismatch')
  if mod=='original' and not passed:original_failed=True
if not original_failed:raise RuntimeError('Original fixture unexpectedly passed')
result={'nonce':NONCE,'cases_passed':len(cases),'original_failed':True,'source_sha256':hashlib.sha256(new.encode()).hexdigest(),'proposal_sha256':hashlib.sha256(patch.encode()).hexdigest(),'format_normalized':False,'model_source_changed':False,'artifact_is_append_only':True,'provider_credentials_present':False,'candidate_separate_uid':True,'parent_compares_results':True}
with open('/dev/ttyS0','w') as out:out.write('\nDAIA_BOOT_RESULT '+json.dumps(result)+'\n')

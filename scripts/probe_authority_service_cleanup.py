"""Credential-free systemd crash probe using the actual subscription stop handler.

Requires the existing daia-egress service identity and Linux systemd. Creates only
a disposable root directory with a synthetic ledger, read-only system libraries,
private networking and no provider credentials. Reports whether the child reached
reservation before SIGKILL and whether ExecStopPost revoked and removed its socket.
"""
import json,os,pwd,shutil,subprocess,tempfile,sys
from pathlib import Path
if os.geteuid()!=0: raise SystemExit('Requires the preconfigured isolated lab administrator')
repo=Path(__file__).resolve().parents[1];sys.path.insert(0,str(repo/'src'))
from daia.request_ledger import create
user=pwd.getpwnam('daia-egress')
root=Path(tempfile.mkdtemp(prefix='daia-authority-service-',dir='/tmp'))
report=[]
try:
 jail=root/'jail';data=root/'authority';shared=root/'endpoint'
 for name in ['usr','run/daia-authority','run/daia-lab','proc/sys/kernel/random','var/lib/daia-lab/templates']:(jail/name).mkdir(parents=True,exist_ok=True)
 for name,target in [('lib','usr/lib'),('lib64','usr/lib64')]: (jail/name).symlink_to(target)
 (jail/'proc/sys/kernel/random/boot_id').touch()
 templates=jail/'var/lib/daia-lab/templates'
 for name in ['model_request.py','model_response.py','model_channel.py','model_upstream.py','codex_https.py','request_ledger.py']:
  shutil.copyfile(repo/'src/daia'/name,templates/name)
 shutil.copyfile(repo/'scripts/probe_subscription_channel_server.py',templates/'public-server.py')
 exercise=templates/'exercise.py';exercise.write_text('''import os,signal,socket,sys,types
from pathlib import Path
p=types.ModuleType('daia');p.__path__=['/var/lib/daia-lab/templates'];sys.modules['daia']=p
from daia.request_ledger import reserve
reserve('/run/daia-authority/requests.json','a'*64)
sock=socket.socket(socket.AF_UNIX);sock.bind('/run/daia-lab/model.sock')
Path('/run/daia-authority/probe-ready.json').write_text(Path('/run/daia-authority/requests.json').read_text())
os.kill(os.getpid(),signal.SIGKILL)
''')
 data.mkdir(mode=0o700);shared.mkdir(mode=0o700)
 create(data/'requests.json','a'*64,seconds=30,requests=6)
 (data/'binding.json').write_text(json.dumps({'binding':'a'*64}));(data/'binding.json').chmod(0o600)
 for path in [data,shared,*data.iterdir()]:os.chown(path,user.pw_uid,user.pw_gid)
 unit='daia-authority-probe-'+root.name.split('-')[-1]
 props={'RootDirectory':str(jail),'BindReadOnlyPaths':'/usr /proc/sys/kernel/random/boot_id',
        'BindPaths':str(data)+':/run/daia-authority '+str(shared)+':/run/daia-lab',
        'User':'daia-egress','Group':str(user.pw_gid),'NoNewPrivileges':'yes','ProtectSystem':'strict',
        'ProtectHome':'yes','ReadWritePaths':'/run/daia-authority /run/daia-lab','PrivateNetwork':'yes',
        'PrivateTmp':'yes','PrivateDevices':'yes','CapabilityBoundingSet':'',
        'MemoryMax':'128M','TasksMax':'16','RuntimeMaxSec':'10','TimeoutStopSec':'3',
        'ExecStopPost':'/usr/bin/python3 -I /var/lib/daia-lab/templates/public-server.py --revoke-only'}
 command=['systemd-run','--quiet','--wait','--collect','--unit='+unit]
 for key,value in props.items():command+=['-p',key+'='+value]
 result=subprocess.run(command+['/usr/bin/python3','-I','/var/lib/daia-lab/templates/exercise.py'],capture_output=True,timeout=25)
 ledger=json.loads((data/'requests.json').read_text())
 marker=data/'revoked.json'
 evidence={'forced_service_exit_nonzero':result.returncode!=0,'child_reserved_before_kill':(data/'probe-ready.json').exists() and json.loads((data/'probe-ready.json').read_text())['remaining']==5,'authority_remaining':ledger['remaining'],
           'stop_handler_persisted_revocation':marker.exists() and json.loads(marker.read_text())=={'persisted':True},
           'model_endpoint_removed':not(shared/'model.sock').exists(), 'private_network':True,
           'real_credentials_used':False,'provider_requests':0}
 print(json.dumps(evidence))
 if not all([evidence['forced_service_exit_nonzero'],evidence['child_reserved_before_kill'],ledger['remaining']==0,evidence['stop_handler_persisted_revocation'],evidence['model_endpoint_removed']]):
  print(result.stderr.decode()[-1500:]);raise RuntimeError('Service revocation probe failed')
finally:
 shutil.rmtree(root)

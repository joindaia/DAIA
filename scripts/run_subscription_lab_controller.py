"""Experimental Linux subscription lab controller; not a participant installer.

Run only through an independently bounded parent service with DAIA_CONTROLLER_UNIT.
Uses existing restricted service identities, KVM/templates and approved public
fixtures. Tests original Codex, refresh and intentionally lost receipt recovery.
Credentials remain outside the VM. No production coordinator or new login is used.
Inputs are trusted operator files, never worker-selected paths or configuration.
"""
import atexit,signal,select,asyncio,json,os,pathlib,pwd,subprocess,sys,tempfile,shutil,socket,selectors,time,threading,uuid
import re
from subscription_lab_outcome import outcome, write_outcome, new_run_directory
from subscription_lab_identity import check_identities
parent_unit=os.environ.get('DAIA_CONTROLLER_UNIT','')
if not re.fullmatch(r'daia-controller-job-[a-f0-9]{32}\.service',parent_unit):
 raise SystemExit('Run inside a dedicated DAIA controller systemd unit.')
def dependent(args):
 return args+['-p','BindsTo='+parent_unit,'-p','After='+parent_unit,'-p','KillMode=control-group','-p','TimeoutStopSec=3','-p','Restart=no']
repo=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(repo/'src'),str(repo/'tests')]
from daia.contributor import Contributor
from daia.mcp_server import build_mcp_app
from daia.service import Coordinator
from daia.store import Store
from daia.assignment_relay import relay as assignment_relay
from test_contributor import direct,invite_file
from test_assignment_host import approve
from test_mcp import running_server
import argparse
parser=argparse.ArgumentParser(description=__doc__)
for name in ('guest','request-template','auth-home','codex-binary','python-runtime'):
 parser.add_argument('--'+name,type=pathlib.Path,required=True)
parser.add_argument('--native-delivery',action='store_true')
parser.add_argument('--crash-before-first-response',action='store_true')
options=parser.parse_args()
if options.crash_before_first_response and not options.native_delivery:parser.error('Crash probe requires native delivery')
# Trusted inputs only. This controller creates no service identities or login.
assert os.geteuid()==0
check_identities()
for value in (v for v in vars(options).values() if isinstance(v,pathlib.Path)):
 assert value.is_absolute() and value.exists() and not value.is_symlink()
 assert re.fullmatch(r'/[A-Za-z0-9_./-]+',str(value)) and '..' not in value.parts
controller=pwd.getpwnam('daia-controller')
for name in ('daia-runtime','daia-egress','daia-research'):pwd.getpwnam(name)
root=pathlib.Path('/var/lib/daia-lab');p=root/'templates';source=options.guest;worker=pwd.getpwnam('daia-runtime')
import hashlib
import runpy
prepare=runpy.run_path(str(repo/'scripts/prepare_kvm_bundle.py'))['prepare']
pinned=json.loads((source/'config.json').read_text())
bundle=root/('subscription-bundle-'+uuid.uuid4().hex)
bundle_hashes=prepare(p/'base.qcow2',source/'seed.iso',bundle,
 base_sha256=pinned['base_sha256'],seed_sha256=pinned['seed_sha256'],nonce=pinned['nonce'])
wrapper=bundle/'report-wrapper.py'
for a,b in [(source/'seed.iso',p/'network-seed.iso'),(source/'config.json',p/'network-config.json'),(source/'probe.py',p/'network-probe.py'),(bundle/'bridge.py',p/'bridge.py')]:shutil.copyfile(a,b);b.chmod(0o444)
rundir=pathlib.Path('/run/daia-lab');endpoint=rundir/'gateway.sock';assert not endpoint.exists()
import ipaddress
for name in ('crash-before-first-response','crash-ready'):(rundir/name).unlink(missing_ok=True)
if options.crash_before_first_response:(rundir/'crash-before-first-response').touch(mode=0o600)
model_socket=rundir/'model.sock';assert not model_socket.exists()
gateway=pwd.getpwnam('daia-egress')
shutil.copyfile(bundle/'model-bridge.py',p/'model-bridge.py');(p/'model-bridge.py').chmod(0o444)
shutil.copyfile(repo/'scripts/probe_subscription_channel_server.py',p/'public-server.py');(p/'public-server.py').chmod(0o444)
for name in ['model_request.py','model_response.py','model_channel.py','model_upstream.py','codex_https.py']:
 shutil.copyfile(repo/'src/daia'/name,p/name);(p/name).chmod(0o444)
shutil.copyfile(options.request_template,p/'model-template.json');(p/'model-template.json').chmod(0o444)
jail=root/'gateway-root'
for name in ['etc','usr','run/daia-lab','var/lib/daia-lab/templates']:(jail/name).mkdir(parents=True,exist_ok=True)
for name,target in [('lib','usr/lib'),('lib64','usr/lib64')]:
 if not (jail/name).is_symlink():(jail/name).symlink_to(target)
shutil.copyfile('/etc/resolv.conf',jail/'etc/resolv.conf');os.chmod(jail/'etc/resolv.conf',0o444)
gunit='daia-egress-'+uuid.uuid4().hex
args=['systemd-run','--unit='+gunit,'--collect','--quiet']
for k,v in {'RootDirectory':str(jail),'BindReadOnlyPaths':'/usr /etc/ssl /var/lib/daia-lab/templates','BindPaths':str(rundir),'User':'daia-egress','Group':str(worker.pw_gid),'NoNewPrivileges':'yes','ProtectSystem':'strict','ProtectHome':'yes','InaccessiblePaths':'/mnt','ReadWritePaths':str(rundir),'PrivateTmp':'yes','ExecStopPost':'/usr/bin/rm -f /run/daia-lab/model.sock','MemoryMax':'128M','MemorySwapMax':'0','TasksMax':'16','RuntimeMaxSec':'240','CapabilityBoundingSet':'','PrivateNetwork':'no','RestrictAddressFamilies':'AF_UNIX AF_INET AF_INET6'}.items():args+=['-p',k+'='+v]
import socket
profile=options.auth_home/'auth.json'
assert profile.stat().st_mode & 0o077 == 0
t=json.loads(profile.read_text())['tokens']
addresses=sorted({x[4][0] for x in socket.getaddrinfo('chatgpt.com',443,family=socket.AF_INET,type=socket.SOCK_STREAM)})
assert addresses and all(ipaddress.ip_address(a).is_global for a in addresses)
args += ['-p','IPAddressDeny=any','-p','IPAddressAllow='+addresses[0]+'/32']
authfile=rundir/'subscription-auth.json'
fd=os.open(authfile,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'w') as f:json.dump({'access_token':t['access_token'],'account_id':t['account_id'],'address':addresses[0]},f)
os.chown(authfile,gateway.pw_uid,gateway.pw_gid);t.clear();authunit=None
for name in ['subscription-audit.json','subscription-request.json']:(rundir/name).unlink(missing_ok=True)

rotation_stop=threading.Event()
rotation_report={}
for name in ['rotation-request','rotation-credential.json','rotation-credential.tmp']:(rundir/name).unlink(missing_ok=True)
def rotate_once():
 try:
  while not rotation_stop.wait(.05):
   if (rundir/'rotation-request').exists():break
  else:return
  (rundir/'rotation-request').unlink()
  original=json.loads(profile.read_text())['tokens']
  owner=pwd.getpwuid(profile.stat().st_uid)
  r=subprocess.run(['/usr/bin/python3',str(repo/'scripts/probe_codex_native_auth.py'),'--binary',str(options.codex_binary),'--home',str(options.auth_home)],user=owner.pw_uid,group=owner.pw_gid,extra_groups=[],env={'PATH':'/usr/bin:/bin'},cwd='/tmp',capture_output=True,timeout=110)
  if r.returncode:raise RuntimeError('native refresh failed')
  report=json.loads(r.stdout)
  assert report['runs'][0]['access_token_changed'] and report['runs'][0]['refresh_token_changed']
  updated=json.loads(profile.read_text())['tokens']
  assert updated['account_id']==original['account_id']
  fd=os.open(rundir/'rotation-credential.tmp',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'w') as f:json.dump({'access_token':updated['access_token']},f)
  os.chown(rundir/'rotation-credential.tmp',gateway.pw_uid,gateway.pw_gid)
  os.replace(rundir/'rotation-credential.tmp',rundir/'rotation-credential.json')
  original.clear();updated.clear()
  rotation_report.update(native_refresh_completed=True,account_unchanged=True,native_restart_completed=report['runs'][1]['chatgpt_account_returned'])
 except Exception as exc:rotation_report['error_type']=type(exc).__name__;print('DAIA_ROTATION_FAILURE',type(exc).__name__,flush=True)
rotation_thread=threading.Thread(target=rotate_once,daemon=True);rotation_thread.start()
def model_cleanup():
 rotation_stop.set();rotation_thread.join(2)
 pathlib.Path('/tmp/daia-rotation-controller-status.json').write_text(json.dumps(rotation_report))
 for name in ['rotation-request','rotation-credential.json','rotation-credential.tmp']:(rundir/name).unlink(missing_ok=True)

 subprocess.run(['systemctl','stop',gunit],capture_output=True,timeout=15)
 model_socket.unlink(missing_ok=True);authfile.unlink(missing_ok=True)
atexit.register(model_cleanup)
subprocess.run(dependent(args)+['/usr/bin/python3','-I',str(p/'public-server.py')],check=True)
for _ in range(100):
 if model_socket.exists():break
 time.sleep(.05)
assert model_socket.exists(),'model service not ready'

researcher=pwd.getpwnam('daia-research')
researchdir=pathlib.Path('/run/daia-research');researchdir.mkdir(mode=0o750,exist_ok=True);os.chown(researchdir,researcher.pw_uid,worker.pw_gid)
assert not (researchdir/'gateway.sock').exists()
for src,dst in [(repo/'src/daia/public_egress.py',p/'public_egress.py'),((repo/'scripts/subscription_lab_research.py'),p/'research-server.py'),((bundle/'research-bridge.py'),p/'research-bridge.py')]:shutil.copyfile(src,dst);dst.chmod(0o444)
interfaces=json.loads(subprocess.check_output(['ip','-j','address'],text=True));excluded=[]
for interface in interfaces:
 for a in interface.get('addr_info',[]):excluded.append(str(ipaddress.ip_network(a['local']+'/'+str(a['prefixlen']),strict=False)))
(p/'egress-policy.json').write_text(json.dumps({'allowed':['docs.python.org','pypi.org','files.pythonhosted.org'],'excluded':excluded}));(p/'egress-policy.json').chmod(0o444)
rjail=root/'research-root'
for name in ['etc','usr','run/daia-research','var/lib/daia-lab/templates']:(rjail/name).mkdir(parents=True,exist_ok=True)
for name,target in [('lib','usr/lib'),('lib64','usr/lib64')]:
 if not (rjail/name).is_symlink():(rjail/name).symlink_to(target)
shutil.copyfile('/etc/resolv.conf',rjail/'etc/resolv.conf')
runit='daia-research-'+uuid.uuid4().hex
researchargs=['systemd-run','--unit='+runit,'--collect','--quiet']
for k,v in {'RootDirectory':str(rjail),'BindReadOnlyPaths':'/usr /var/lib/daia-lab/templates','BindPaths':str(researchdir),'User':'daia-research','Group':str(worker.pw_gid),'NoNewPrivileges':'yes','ProtectSystem':'strict','ProtectHome':'yes','PrivateTmp':'yes','PrivateDevices':'yes','CapabilityBoundingSet':'','ReadWritePaths':str(researchdir),'ExecStopPost':'/usr/bin/rm -f /run/daia-research/gateway.sock','MemoryMax':'128M','MemorySwapMax':'0','TasksMax':'16','RuntimeMaxSec':'240','RestrictAddressFamilies':'AF_UNIX AF_INET AF_INET6'}.items():researchargs+=['-p',k+'='+v]
def research_cleanup():
 subprocess.run(['systemctl','stop',runit],capture_output=True,timeout=15);(researchdir/'gateway.sock').unlink(missing_ok=True)
atexit.register(research_cleanup)
subprocess.run(dependent(researchargs)+['/usr/bin/python3','-I',str(p/'research-server.py')],check=True)
for _ in range(100):
 if (researchdir/'gateway.sock').exists():break
 time.sleep(.05)
assert (researchdir/'gateway.sock').exists()

run_state=new_run_directory(root/'runs')
private=run_state/'assignment';coordinator_dir=run_state/'coordinator'
write_outcome('/run/daia-subscription-run.json',{'state_directory':str(run_state), 'automatic_resume_authorized':False})
service=Coordinator(Store(str(coordinator_dir/'network.sqlite3')));service.admit_evidence({'objective': 'Find the numeric-version comparison bug in this frozen public fixture.', 'baseline_commit': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'source': {'path': 'src/version_check.py', 'start_line': 1, 'text': 'def newer(a, b): return a > b\n'}})
with running_server(build_mcp_app(service)) as url:
 invite=invite_file(private,service,url);host=direct(Contributor(invite,minutes=5),service)
 lease=asyncio.run(host.perform('request_work'))
 write_outcome(run_state/'run.json',{'assignment_id':lease['assignment_id'], 'automatic_resume_authorized':False})
 before={k:host.state[k] for k in ['key','used','deadline','max_jobs']}
 # Freeze before helper/VM startup. Neither connection nor heartbeat resets it.
 remaining=min(150,lease['hard_deadline']-host.clock(),host.state['deadline']-host.clock())
 if remaining<=0:raise RuntimeError('Assignment transport already expired')
 transport_deadline=time.monotonic()+remaining
 cfg=private/'helper.json';cfg.write_text(json.dumps({'invite':'/state/'+invite.name,'assignment':lease['assignment_id'],'authority':approve(host,lease,['read_input','heartbeat','submit_result'])}));cfg.chmod(0o600)
 os.chown(private,controller.pw_uid,controller.pw_gid)
 for entry in private.iterdir():os.chown(entry,controller.pw_uid,controller.pw_gid);entry.chmod(0o600)
 jail=root/('controller-root-'+uuid.uuid4().hex)
 for name in ['usr','opt/runtime','opt/source','state','tmp']:(jail/name).mkdir(parents=True,exist_ok=True)
 for name,target in [('lib','usr/lib'),('lib64','usr/lib64'),('bin','usr/bin')]: (jail/name).symlink_to(target)
 (jail/'opt/helper.py').touch()
 helperunit='daia-controller-'+uuid.uuid4().hex
 helperargs=['systemd-run','--unit='+helperunit,'--pipe','--wait','--quiet','--collect','--setenv=PYTHONPATH=/opt/source']
 props={'RootDirectory':str(jail),'BindReadOnlyPaths':'/usr '+str(options.python_runtime)+':/opt/runtime '+str(repo/'src')+':/opt/source '+str(repo/'scripts/subscription_lab_helper.py')+':/opt/helper.py','BindPaths':str(private)+':/state','User':'daia-controller','Group':str(controller.pw_gid),'WorkingDirectory':'/state','NoNewPrivileges':'yes','ProtectSystem':'strict','ProtectHome':'yes','PrivateTmp':'yes','PrivateDevices':'yes','ReadWritePaths':'/state','CapabilityBoundingSet':'','RestrictAddressFamilies':'AF_INET AF_UNIX','IPAddressDeny':'any','IPAddressAllow':'localhost','MemoryMax':'256M','MemorySwapMax':'0','TasksMax':'32','RuntimeMaxSec':'240','TimeoutStopSec':'3','KillMode':'control-group'}
 for k,v in props.items():helperargs+=['-p',k+'='+v]
 helper=None;unit=None
 def cleanup():
  units=[x for x in (unit,helperunit) if x]
  if units:
   try:subprocess.run(['systemctl','stop',*units],capture_output=True,timeout=15)
   except subprocess.TimeoutExpired:pass  # Independent unit RuntimeMaxSec still applies.
  endpoint.unlink(missing_ok=True)
  if helper is not None:
   if helper.poll() is None:helper.terminate()
   try:helper.communicate(timeout=5)
   except subprocess.TimeoutExpired:helper.kill();helper.communicate(timeout=5)
 atexit.register(cleanup)
 signal.signal(signal.SIGTERM,lambda *_:sys.exit(143))
 helper=subprocess.Popen(dependent(helperargs)+['/opt/runtime/bin/python','-B','/opt/helper.py','/state/helper.json'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 for _ in range(100):
  if (private/'runtime-check.json').exists():break
  if helper.poll() is not None: raise AssertionError('helper startup failed: '+helper.stderr.read(2000).decode(errors='replace'))
  time.sleep(.1)
 assert (private/'runtime-check.json').exists(),'helper not ready'
 runtime_check=json.loads((private/'runtime-check.json').read_text());assert runtime_check['nonroot'] and runtime_check['personal_mount_absent']
 for account in ['daia-runtime','daia-egress','daia-research']:
  u=pwd.getpwnam(account)
  result=subprocess.run(['/usr/bin/python3','-c','import os,sys;assert not os.access(sys.argv[1],os.R_OK)',str(host.path)],user=u.pw_uid,group=u.pw_gid,extra_groups=[],capture_output=True)
  assert result.returncode==0,'another service can read helper key state'

 errors=[]
 with socket.socket(socket.AF_UNIX) as listener:
  listener.bind(str(endpoint));os.chown(endpoint,0,worker.pw_gid);endpoint.chmod(0o660);listener.listen(1)
  def relay():
   try:
    remaining=transport_deadline-time.monotonic()
    if remaining<=0:raise TimeoutError('Assignment transport expired before accept')
    listener.settimeout(remaining)
    connection,_=listener.accept()
    with connection:
     if assignment_relay(connection,helper,seconds=150,max_bytes=256*1024,
                         deadline=transport_deadline)!='complete':
      raise TimeoutError('Assignment transport expired')
   except Exception as exc:errors.append(type(exc).__name__)
  thread=threading.Thread(target=relay,daemon=True);thread.start()
  job=root/('job-'+uuid.uuid4().hex);job.mkdir(mode=0o700);os.chown(job,worker.pw_uid,worker.pw_gid);unit='daia-assignment-'+uuid.uuid4().hex
  pathlib.Path('/tmp/daia-live-dual-last.json').write_text(json.dumps({'job':str(job),'unit':unit,'helper_unit':helperunit}))
  args=['systemd-run','--unit='+unit,'--wait','--pipe','--collect']
  props={'User':'daia-runtime','Group':str(worker.pw_gid),'SupplementaryGroups':'kvm','WorkingDirectory':str(job),'NoNewPrivileges':'yes','ProtectSystem':'strict','ProtectHome':'yes','InaccessiblePaths':'/mnt','ReadWritePaths':str(job),'ExecStopPost':'/usr/bin/rm -f -- '+str(job/'guest.qcow2'),'PrivateNetwork':'yes','PrivateTmp':'yes','DevicePolicy':'closed','DeviceAllow':'/dev/kvm rw','MemoryMax':'3G','TasksMax':'128','RuntimeMaxSec':'210','TimeoutStopSec':'5','KillMode':'control-group','CapabilityBoundingSet':''}
  props.pop('ReadWritePaths',None);props.pop('PrivateTmp',None)
  def mount_options(size,inodes):
   return f'size={size},nr_inodes={inodes},mode=0700,uid={worker.pw_uid},gid={worker.pw_gid},nodev,nosuid,noexec'
  props['TemporaryFileSystem']=str(job)+':'+mount_options('512M',4096)+' '+' '.join(n+':'+mount_options('16M',256) for n in ('/tmp','/var/tmp','/dev/shm'))
  props['PrivateIPC']='yes';props['MemorySwapMax']='0';props['TasksMax']='64'
  for k,v in props.items():args+=['-p',k+'='+v]
  crash_info={};crash_stop=threading.Event()
  first_unit=unit
  def crash_worker():
   while not crash_stop.wait(.02):
    if (rundir/'crash-ready').exists():
     killed=subprocess.run(['systemctl','kill','--signal=SIGKILL','--kill-whom=all',first_unit],capture_output=True,timeout=5)
     crash_info['kill_succeeded']=killed.returncode==0
     (rundir/'crash-before-first-response').unlink(missing_ok=True)
     return
  crash_thread=None
  if options.crash_before_first_response:
   crash_thread=threading.Thread(target=crash_worker,daemon=True);crash_thread.start()
  try:
   r=subprocess.run(dependent(args)+['/usr/bin/python3','-I',str(wrapper),'--bundle',str(bundle)],capture_output=True,timeout=220)
   if options.crash_before_first_response:
    crash_stop.set();crash_thread.join(6)
    if r.returncode==0 or not crash_info.get('kill_succeeded'):
     fd=os.open('/run/daia-subscription-failure-private.json',os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
     with os.fdopen(fd,'wb') as capture:capture.write(r.stdout[:64*1024])
     raise RuntimeError('Crash injection not reached; private worker diagnostics retained')
    thread.join(5);assert not thread.is_alive()
    assert not any(job.iterdir()),'Killed worker storage survived'
    prior=json.loads(host.path.read_text())
    assert {k:prior[k] for k in before}==before and prior['pending'] is None
    assert service.metrics()['results']==0
    initial={}
    for _ in range(100):
     if (rundir/'subscription-audit.json').exists():
      initial=json.loads((rundir/'subscription-audit.json').read_text())
      if initial['forwarded']==1:break
     time.sleep(.02)
    assert initial['forwarded']==initial['attempts']==1
    subprocess.run(['systemctl','stop',helperunit],capture_output=True,timeout=10)
    helper.communicate(timeout=5)
    old_helper=helperunit;helperunit='daia-controller-'+uuid.uuid4().hex
    helperargs=[x.replace(old_helper,helperunit) for x in helperargs]
    (private/'runtime-check.json').unlink(missing_ok=True)
    helper=subprocess.Popen(dependent(helperargs)+['/opt/runtime/bin/python','-B','/opt/helper.py','/state/helper.json'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    for _ in range(100):
     if (private/'runtime-check.json').exists():break
     time.sleep(.05)
    assert (private/'runtime-check.json').exists() and helper.poll() is None
    errors.clear();thread=threading.Thread(target=relay,daemon=True);thread.start()
    old_job=job;old_unit=unit
    job=root/('job-'+uuid.uuid4().hex);job.mkdir(mode=0o700);os.chown(job,worker.pw_uid,worker.pw_gid)
    unit='daia-assignment-'+uuid.uuid4().hex
    args=[x.replace(str(old_job),str(job)).replace(old_unit,unit) for x in args]
    crash_info.update(fresh_worker_directory=True,old_storage_removed=True,
                      same_assignment=True,provider_calls_before_restart=1,
                      gateway_restarted=False,transport_deadline_reset=False)
    r=subprocess.run(dependent(args)+['/usr/bin/python3','-I',str(wrapper),'--bundle',str(bundle)],capture_output=True,timeout=220)
   if r.returncode:
    fd=os.open('/run/daia-subscription-failure-private.json',os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'wb') as capture:capture.write(r.stdout[:64*1024])
    thread.join(5)
    saved_failure=json.loads(host.path.read_text())
    with service.store.connect() as db:
     assignment_failure=db.execute('SELECT id,state,receipt_hash FROM assignments WHERE id=?', (lease['assignment_id'],)).fetchone()
    failure_outcome=outcome(saved_failure,dict(assignment_failure) if assignment_failure else None)
    write_outcome(private/'outcome.json',failure_outcome)
    write_outcome('/run/daia-subscription-outcome.json',failure_outcome)
    raise RuntimeError('Worker failed; private diagnostics and delivery outcome retained')
   thread.join(5);assert not thread.is_alive() and not errors
   saved=json.loads(host.path.read_text());assert {k:saved[k] for k in before}==before
   assert saved['pending'] is None and saved['lease'] is None
   assert service.metrics()['results']==1
   assert not any(job.iterdir())
   assert len(r.stdout)<=9*1024*1024
   envelope=json.loads(r.stdout);assert envelope['ok'] is True
   report=envelope['report'];assert options.native_delivery or report['guest']['receipt_hash']==saved['receipt']['receipt_hash']
   if options.native_delivery:
    audit=json.loads((private/'delivery-audit.json').read_text())
    submissions=[a for a in audit if a['operation']=='submit_result']
    assert report['guest']['native_mcp_delivery']
    assert any(a['operation']=='heartbeat' for a in audit)
    assert len(submissions)==2 and submissions[0].get('receipt_hidden')
    assert submissions[1]['status']=='already_recorded'
    report['guest']['receipt_hash']=saved['receipt']['receipt_hash']
    report['native_delivery_audit']=audit
    report['delivery_origin']='native_codex_mcp'
   else:
    assert report['guest']['scoped_tools'] and report['guest']['wrong_retry_denied'] and report['guest']['exact_retry']
    report['delivery_origin']='fixture_harness'
   report['assembled_bundle_sha256']=bundle_hashes
   report['bounded_storage_and_export']=True
   model_audit=json.loads((rundir/'subscription-audit.json').read_text())
   model_counts={k:model_audit[k] for k in ['forwarded','denied','attempts']}
   assert 1<=model_counts['forwarded']<=6
   assert model_counts['denied'] in ((46,47) if options.crash_before_first_response else (23,))
   if options.crash_before_first_response:report['worker_crash_recovery']=crash_info
   assert model_audit.get('credential_rotated') and model_audit.get('deadline_preserved')
   assert rotation_report.get('native_refresh_completed') and 'error_type' not in rotation_report
   report['rotation']=dict(rotation_report,deadline_preserved=True,rotation_after_provider_requests=1)
   report['model_channel_counts']=model_counts
   report['provider_credentials_used']=True
   report.update({'saved_identity_and_consent_unchanged':True,'results':1,'pending_cleared_after_exact_receipt':True,'synthetic_fixture':True,'real_model':True,'helper_nonroot':True,'helper_private_root':True,'other_service_state_read_denied':True})
   pathlib.Path('/tmp/daia-live-research-result.json').write_text(json.dumps(report));print(json.dumps(report))
  finally:
   crash_stop.set()
   if crash_thread:crash_thread.join(6)
   endpoint.unlink(missing_ok=True);subprocess.run(['systemctl','stop',helperunit],capture_output=True);helper.terminate()
   try:helper.communicate(timeout=5)
   except subprocess.TimeoutExpired:helper.kill();helper.communicate(timeout=5)

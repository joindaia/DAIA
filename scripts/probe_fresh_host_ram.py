"""Credential-free fresh-host provisioning probe in a networkless RAM-backed VM.

Trusted administrator in the existing dedicated Linux lab only. Reuses the pinned
base and host KVM/QEMU; this is not a full installer or a hostile-code test.
No participant login, provider traffic, host account changes or disk overlay.
"""
import pathlib,json,subprocess,tempfile,os,pwd,hashlib,uuid,shutil


def main():
 if not __debug__ or os.geteuid()!=0:
  raise SystemExit('Normal Python and trusted lab administrator required')
 repo=pathlib.Path(__file__).resolve().parents[1]
 SYSUSERS=(repo/'deploy/subscription-lab/daia-lab.sysusers.conf').read_text()
 TMPFILES=(repo/'deploy/subscription-lab/daia-lab.tmpfiles.conf').read_text()
 GUEST=(repo/'scripts/fresh_host_guest.py').read_text()
 P=pathlib.Path
 assert any(x.split()[4]=='/run' and ' - tmpfs ' in x for x in P('/proc/self/mountinfo').read_text().splitlines())
 assert int(next(x.split()[1] for x in P('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))>5*1024*1024
 base=P('/var/lib/daia-lab/templates/base.qcow2')
 with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354'
 worker=pwd.getpwnam('daia-runtime');nonce=uuid.uuid4().hex;unit='daia-fresh-host-'+nonce
 with tempfile.TemporaryDirectory(dir='/run',prefix='daia-fresh-host-') as folder:
  root=P(folder);root.chmod(0o755);work=root/'work';work.mkdir();work.chmod(0o755)
  cloud={'users':[],'package_update':False,'package_upgrade':False,'write_files':[{'path':'/etc/sysusers.d/daia.conf','content':SYSUSERS},{'path':'/etc/tmpfiles.d/daia.conf','content':TMPFILES},{'path':'/tmp/fresh.py','content':GUEST.replace('NONCE',nonce)}],'runcmd':[['python3','/tmp/fresh.py']],'power_state':{'mode':'poweroff','delay':'now','timeout':30,'condition':True}}
  (root/'user-data').write_text('#cloud-config\n'+json.dumps(cloud));(root/'meta-data').write_text('instance-id: '+nonce+'\n');(root/'network-config').write_text(json.dumps({'version':2,'ethernets':{'unused':{'match':{'name':'en*'},'dhcp4':False,'dhcp6':False,'optional':True}}}))
  subprocess.run(['genisoimage','-quiet','-output',str(root/'seed.iso'),'-volid','CIDATA','-joliet','-rock',*[str(root/x) for x in ['user-data','meta-data','network-config']]],check=True,capture_output=True)
  runner=r"""
 import pathlib,subprocess,json,sys
 p=pathlib.Path('.')
 subprocess.run(['qemu-img','create','-q','-f','qcow2','-F','qcow2','-b',sys.argv[1],'guest.qcow2'],check=True)
 try:
  r=subprocess.run(['qemu-system-x86_64','-no-user-config','-nodefaults','-machine','q35','-accel','kvm','-cpu','host','-m','2048','-smp','2','-display','none','-nic','none','-monitor','none','-no-reboot','-drive','file=guest.qcow2,if=virtio,format=qcow2','-drive','file='+sys.argv[2]+',media=cdrom,readonly=on','-serial','file:serial.txt'],capture_output=True,timeout=150)
  assert r.returncode==0
  with p.joinpath('serial.txt').open('rb') as stream:raw=stream.read(4*1024*1024+1)
  assert len(raw)<4*1024*1024
  rows=[json.loads(x.split('DAIA_FRESH_HOST ',1)[1]) for x in raw.decode(errors='replace').splitlines() if __import__('re').fullmatch(r'(?:\[\s*[0-9.]+\] cloud-init\[[0-9]+\]: )?DAIA_FRESH_HOST .+',x)]
  assert len(rows)==1 and rows[0]['nonce']==sys.argv[3], 'Guest provisioning report missing'
  print(json.dumps(rows[0]),flush=True)
 except BaseException as error:
  serial=p/'serial.txt'
  raw=b''
  if serial.exists():
   with serial.open('rb') as stream:raw=stream.read(4*1024*1024+1)
  print(json.dumps({'failed':type(error).__name__,'serial_bytes':len(raw),'serial_findings':[line for line in raw.decode(errors='replace').splitlines() if any(word in line for word in ('DAIA_FRESH','Traceback','fresh.py','AssertionError','Error:','CalledProcessError','modprobe','scripts-user'))][-35:]}),flush=True)
  raise
 finally:p.joinpath('guest.qcow2').unlink(missing_ok=True)
 """
  (root/'runner.py').write_text(__import__('textwrap').dedent(runner))
  props={'User':str(worker.pw_uid),'Group':str(worker.pw_gid),'SupplementaryGroups':'kvm','WorkingDirectory':str(work),'TemporaryFileSystem':str(work)+':size=512M,nr_inodes=4096,mode=0700,uid='+str(worker.pw_uid)+',gid='+str(worker.pw_gid),'NoNewPrivileges':'yes','ProtectSystem':'strict','ProtectHome':'yes','InaccessiblePaths':'/mnt','PrivateNetwork':'yes','PrivateTmp':'yes','DevicePolicy':'closed','DeviceAllow':'/dev/kvm rw','CapabilityBoundingSet':'','MemoryMax':'3G','MemorySwapMax':'0','TasksMax':'64','RuntimeMaxSec':'170','TimeoutStopSec':'5','KillMode':'control-group'}
  command=['systemd-run','--quiet','--unit='+unit,'--wait','--pipe']
  for k,v in props.items():command+=['-p',k+'='+v]
  command+=['/usr/bin/python3','-I',str(root/'runner.py'),str(base),str(root/'seed.iso'),nonce]
  try:
   result=subprocess.run(command,capture_output=True,text=True,timeout=180)
   print(json.dumps({'returncode':result.returncode,'guest_report':result.stdout.strip(),'error_tail':result.stderr[-700:],'provider_used':False,'network_enabled':False,'overlay_ram_limit_mib':512}))
   if result.returncode:raise RuntimeError('Fresh-host probe failed')
  finally:
   subprocess.run(['systemctl','stop',unit],capture_output=True,timeout=15)
   active=subprocess.run(['systemctl','is-active',unit],capture_output=True,text=True).stdout.strip()
   assert active not in ('active','activating','deactivating')
   assert not list(work.iterdir())
   subprocess.run(['systemctl','reset-failed',unit],capture_output=True)
   print(json.dumps({'stopped':True,'ram_overlay_removed':True}))

if __name__=='__main__':
 main()

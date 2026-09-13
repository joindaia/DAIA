"""Trusted Linux lab driver for a service-private KVM work mount.

The operator supplies the prepared credential-free boot-test bundle containing
launcher.py and its pinned inputs. This does not prepare images or authenticate
a participant. Results are printed for a trusted parent to capture.
"""
from pathlib import Path
import json,os,pwd,subprocess,tempfile,uuid,argparse
account=pwd.getpwnam('daia-runtime')
parser=argparse.ArgumentParser(description='Credential-free KVM storage probe; requires a trusted prepared boot-test bundle.')
parser.add_argument('--bundle',required=True)
bundle=Path(parser.parse_args().bundle).resolve(strict=True)
assert os.getuid()==0
with tempfile.TemporaryDirectory(prefix='daia-kvm-storage-',dir='/run') as name:
 root=Path(name);root.chmod(0o755);work=root/'work';work.mkdir(mode=0o700);os.chown(work,account.pw_uid,account.pw_gid)
 wrapper=root/'check.py'
 wrapper.write_text("import subprocess,json,os\nfrom pathlib import Path\ns=os.statvfs('.')\nassert 0<s.f_blocks*s.f_frsize<=512*1024*1024\nsubprocess.run(['/usr/bin/python3','-I',"+repr(str(bundle/'launcher.py'))+",'--bundle',"+repr(str(bundle))+"],check=True,timeout=195)\nr=json.loads(Path('report.json').read_text());assert r['guest']['booted'] and r['overlay_removed']\nprint(json.dumps({'real_kvm_boot':True,'filesystem_limit_bytes':s.f_blocks*s.f_frsize,'filesystem_inode_limit':s.f_files,'overlay_removed':True,'private_report_read_before_teardown':True,'files_remaining_inside':len(list(Path('.').iterdir()))}))\n")
 wrapper.chmod(0o444);unit='daia-kvm-storage-'+uuid.uuid4().hex
 opts=f'size=512M,nr_inodes=4096,mode=0700,uid={account.pw_uid},gid={account.pw_gid},nodev,nosuid,noexec'
 props={'User':'daia-runtime','Group':str(account.pw_gid),'SupplementaryGroups':'kvm','WorkingDirectory':str(work),'TemporaryFileSystem':str(work)+':'+opts,'ProtectSystem':'strict','ProtectHome':'yes','PrivateTmp':'yes','PrivateNetwork':'yes','NoNewPrivileges':'yes','CapabilityBoundingSet':'','DevicePolicy':'closed','DeviceAllow':'/dev/kvm rw','MemoryMax':'3G','MemorySwapMax':'0','TasksMax':'64','RuntimeMaxSec':'210','TimeoutStopSec':'5','KillMode':'control-group'}
 args=['systemd-run','--quiet','--wait','--pipe','--collect','--unit='+unit]
 for k,v in props.items():args+=['-p',k+'='+v]
 try:
  r=subprocess.run(args+['/usr/bin/python3','-I',str(wrapper)],capture_output=True,timeout=230)
  if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-2000:])
  report=json.loads(r.stdout.splitlines()[-1]);assert not any(work.iterdir());report['host_directory_unchanged']=True
  print(json.dumps(report))
 finally:subprocess.run(['systemctl','stop',unit],capture_output=True,timeout=10)

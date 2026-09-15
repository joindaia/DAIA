"""Trusted, credential-free provisioning fixture; execute only inside the fresh VM."""
import json,pwd,pathlib,subprocess,os,fcntl
P=pathlib.Path
names=['daia-controller','daia-runtime','daia-egress','daia-research']
assert all(n not in {a.pw_name for a in pwd.getpwall()} for n in names)
assert P('/proc/1/comm').read_text().strip()=='systemd'
for _ in range(2):
 subprocess.run(['systemd-sysusers','/etc/sysusers.d/daia.conf'],check=True,capture_output=True)
 subprocess.run(['systemd-tmpfiles','--create','/etc/tmpfiles.d/daia.conf'],check=True,capture_output=True)
 accounts=[pwd.getpwnam(n) for n in names]
 assert len({a.pw_uid for a in accounts})==4 and all(a.pw_uid!=0 and a.pw_shell=='/usr/sbin/nologin' for a in accounts)
 state=P('/etc/passwd').read_bytes()
 if _==0:before=state
 else:assert before==state
for path,mode in [('/var/lib/daia-lab',0o755),('/var/lib/daia-lab/templates',0o755),('/var/lib/daia-lab/runs',0o700),('/run/daia-lab',0o750),('/run/daia-research',0o750)]:
 assert P(path).stat().st_mode&0o777==mode
subprocess.run(['modprobe','kvm_intel'],check=True,capture_output=True)
fd=os.open('/dev/kvm',os.O_RDWR)
try: api=fcntl.ioctl(fd,0xAE00,0)
finally:os.close(fd)
assert api==12
print('DAIA_FRESH_HOST '+json.dumps({'fresh_accounts':True,'native_manifests_installed':True,'repeat_idempotent':True,'directories_checked':5,'nested_kvm_api':api,'nonce':'NONCE'}),flush=True)

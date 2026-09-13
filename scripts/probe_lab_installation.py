"""Create and remove an isolated temporary filesystem root to test lab manifests.

Uses native systemd tools with --root for every operation. Never installs into
host /etc or starts a service. No provider credentials, login or jobs involved.
Run only on the trusted Linux installation side, not as an untrusted worker tool.
"""
import tempfile,pathlib,subprocess,json,hashlib,os
repo=pathlib.Path(__file__).resolve().parents[1]
if os.geteuid()!=0: raise SystemExit('Administrator required for temporary-root ownership checks')
host_before={p:pathlib.Path(p).read_bytes() for p in ('/etc/passwd','/etc/group')}
with tempfile.TemporaryDirectory(prefix='daia-empty-system-') as name:
 root=pathlib.Path(name);(root/'etc').mkdir()
 (root/'etc/passwd').write_text('root:x:0:0:root:/root:/bin/sh\n')
 (root/'etc/group').write_text('root:x:0:\n')
 config=repo/'deploy/subscription-lab'
 first=None
 for _ in range(2):
  subprocess.run(['systemd-sysusers','--root='+name,str(config/'daia-lab.sysusers.conf')],check=True,capture_output=True)
  subprocess.run(['systemd-tmpfiles','--root='+name,'--create',str(config/'daia-lab.tmpfiles.conf')],check=True,capture_output=True)
  state=[(root/'etc'/p).read_bytes() for p in ('passwd','group')]
  if first is None:first=state
  else:assert state==first
 accounts={x.split(':')[0]:x.split(':') for x in (root/'etc/passwd').read_text().splitlines()}
 names=['daia-controller','daia-runtime','daia-egress','daia-research']
 assert len({accounts[n][2] for n in names})==4
 assert all(accounts[n][2]!='0' and accounts[n][-1]=='/usr/sbin/nologin' for n in names)
 for p,mode,owner,group in [('var/lib/daia-lab',0o755,'root','root'),('var/lib/daia-lab/templates',0o755,'root','root'),('var/lib/daia-lab/runs',0o700,'root','root'),('run/daia-lab',0o750,'daia-egress','daia-runtime'),('run/daia-research',0o750,'daia-research','daia-runtime')]:
  st=(root/p).stat();assert st.st_mode&0o777==mode and st.st_uid==int(accounts[owner][2]) and st.st_gid==int(accounts[group][3])
 assert all(pathlib.Path(p).read_bytes()==v for p,v in host_before.items())
 print(json.dumps({'empty_root_install':True,'repeated_install':True,'distinct_nonroot_accounts':4,'verified_directories':5,'host_accounts_modified':False,'credentials_used':False}))

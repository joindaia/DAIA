"""Credential-free real-KVM crash/clean-restart test for four bounded mounts.

Trusted Linux lab administrator only. Requires an approved boot-test bundle;
no provider login, assignment credentials or external connections are used.
"""
import argparse
import json
import os
from pathlib import Path
import pwd
import subprocess
import tempfile
import time
import uuid


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True)
    args=parser.parse_args()
    assert os.getuid()==0
    bundle=Path(args.bundle).resolve(strict=True)
    nonce=json.loads((bundle/'network-config.json').read_text())['nonce']
    user=pwd.getpwnam('daia-runtime')
    def run(*args):
        return subprocess.run(args,check=True,capture_output=True,text=True,timeout=10).stdout.strip()
    def show(unit,key):return run('systemctl','show',unit,'-p',key,'--value')
    with tempfile.TemporaryDirectory(prefix='daia-storage-crash-',dir='/run') as directory:
        root=Path(directory);root.chmod(0o755)
        work=root/'work';work.mkdir(mode=0o700);os.chown(work,user.pw_uid,user.pw_gid)
        marker='state-'+uuid.uuid4().hex
        paths=[str(work),'/tmp','/var/tmp','/dev/shm']
        wrapper=root/'run.py'
        wrapper.write_text("import subprocess,threading,time\nfrom pathlib import Path\n"
            "def mark():\n while not Path('guest.qcow2').exists():time.sleep(.01)\n"
            " for p in "+repr(paths)+":(Path(p)/"+repr(marker)+").write_text('synthetic-runtime-state')\n"
            "threading.Thread(target=mark,daemon=True).start()\n"
            "subprocess.run(['/usr/bin/python3','-I',"+repr(str(bundle/'launcher.py'))+",'--bundle',"+repr(str(bundle))+"],check=True,timeout=195)\n")
        wrapper.chmod(0o444)
        unit='daia-storage-crash-'+uuid.uuid4().hex
        freshunit=unit+'-fresh'
        def command(unit):
            options=lambda size,inodes:f'size={size},nr_inodes={inodes},mode=0700,uid={user.pw_uid},gid={user.pw_gid},nodev,nosuid,noexec'
            mounts=str(work)+':'+options('512M',4096)+' '+' '.join(p+':'+options('16M',256) for p in paths[1:])
            props={'User':'daia-runtime','Group':str(user.pw_gid),'SupplementaryGroups':'kvm','WorkingDirectory':str(work),
                   'TemporaryFileSystem':mounts,'ProtectSystem':'strict','ProtectHome':'yes','PrivateIPC':'yes',
                   'PrivateNetwork':'yes','NoNewPrivileges':'yes','CapabilityBoundingSet':'','DevicePolicy':'closed',
                   'DeviceAllow':'/dev/kvm rw','MemoryMax':'3G','MemorySwapMax':'0','TasksMax':'64',
                   'RuntimeMaxSec':'210','TimeoutStopSec':'5','KillMode':'control-group','Type':'exec'}
            cmd=['systemd-run','--quiet','--unit='+unit]
            for k,v in props.items():cmd+=['-p',k+'='+v]
            return cmd
        try:
            run(*command(unit),'/usr/bin/python3','-I',str(wrapper))
            deadline=time.monotonic()+180
            while time.monotonic()<deadline:
                pid=int(show(unit,'MainPID') or '0')
                if not pid:raise RuntimeError('Service ended before crash readiness')
                view=Path('/proc')/str(pid)/'root'
                serial=view/str(work).lstrip('/')/'serial.txt'
                if serial.exists():
                    lines=serial.read_text(errors='replace').splitlines()
                    results=[json.loads(x[17:]) for x in lines if x.startswith('DAIA_BOOT_RESULT ')]
                    if results and results[0].get('nonce')==nonce:break
                time.sleep(.1)
            else:raise TimeoutError('Guest readiness')
            group=show(unit,'ControlGroup');cg=Path('/sys/fs/cgroup'+group)
            pids={int(x) for p in cg.rglob('cgroup.procs') for x in p.read_text().split()}
            assert any((Path('/proc')/str(p)/'comm').read_text().startswith('qemu-system') for p in pids)
            assert all((view/p.lstrip('/')/marker).read_text()=='synthetic-runtime-state' for p in paths)
            assert (view/str(work).lstrip('/')/'guest.qcow2').exists()
            started=time.monotonic()
            run('systemctl','kill','--kill-whom=main','--signal=KILL',unit)
            while time.monotonic()-started<12:
                events=cg/'cgroup.events'
                if not events.exists() or 'populated 1' not in events.read_text():break
                time.sleep(.05)
            assert not (cg/'cgroup.events').exists() or 'populated 1' not in (cg/'cgroup.events').read_text()
            assert not any((Path('/proc')/str(p)).exists() for p in pids)
            assert show(unit,'ExecMainCode')=='2' and show(unit,'ExecMainStatus')=='9'
            assert not any(work.iterdir())
            elapsed=round(time.monotonic()-started,3)
            fresh=root/'fresh.py'
            fresh.write_text("from pathlib import Path\nimport json\npaths="+repr(paths)+"\n"
                "assert len({Path(p).stat().st_dev for p in paths})==4\n"
                "for p in paths:\n assert not any(Path(p).iterdir())\n (Path(p)/'control').write_text('fresh')\n"
                "print(json.dumps({'fresh_four_mounts_empty':True,'fresh_writes_succeeded':True}))\n")
            fresh.chmod(0o444)
            result=subprocess.run(command(freshunit)+['--wait','--pipe','/usr/bin/python3','-I',str(fresh)],capture_output=True,timeout=30)
            assert result.returncode==0,result.stderr.decode(errors='replace')[-1000:]
            assert not any(work.iterdir())
            report={'real_kvm_running_before_kill':True,'state_in_all_four_mounts_before_kill':True,
                    'main_killed_with_sigkill':True,'cgroup_empty':True,'recorded_processes_gone':True,
                    'host_directory_unchanged':True,'termination_seconds':elapsed,
                    'restart':json.loads(result.stdout),'credentials_used':False,'model_requests':0}
            print(json.dumps(report))
        finally:
            subprocess.run(['systemctl','stop',unit,freshunit],capture_output=True,timeout=15)
            subprocess.run(['systemctl','reset-failed',unit,freshunit],capture_output=True,timeout=10)


if __name__=='__main__':main()

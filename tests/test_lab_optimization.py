"""Every guarded lab entrypoint refuses optimization before dependencies/actions."""
import os
from pathlib import Path
import subprocess
import sys
import pytest

NAMES = ['run_subscription_lab.py','run_subscription_lab_controller.py',
         'subscription_lab_helper.py','probe_subscription_channel_server.py',
         'probe_pending_receipt_lab.py','probe_lab_installation.py']


@pytest.mark.parametrize('name',NAMES)
@pytest.mark.parametrize('mode',['flag','environment'])
def test_optimized_entrypoint_stops_before_imports_or_side_effects(tmp_path,name,mode):
    script=Path(__file__).parents[1]/'scripts'/name
    env=dict(os.environ)
    env.pop('PYTHONPATH',None)
    args=[sys.executable]
    if mode=='flag': args+=['-I','-O']
    else: env['PYTHONOPTIMIZE']='2'
    result=subprocess.run([*args,str(script)],cwd=tmp_path,env=env,
                          capture_output=True,text=True,timeout=5)
    assert result.returncode!=0
    assert result.stdout==''
    assert result.stderr.strip()=='Optimized Python is unsupported for lab execution'
    assert list(tmp_path.iterdir())==[]

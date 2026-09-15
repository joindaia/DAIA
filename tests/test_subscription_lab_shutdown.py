"""Post-stop evidence must belong to this controller and remain private/read-only."""
import json
import os
from pathlib import Path
import runpy
import sys
import pytest

if sys.platform != 'linux':
    pytest.skip('Linux supervised lab shutdown', allow_module_level=True)

VERIFY = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/subscription_lab_shutdown.py'))['verify']
UNIT = 'daia-controller-job-' + 'a'*32 + '.service'


def setup(tmp_path):
    tmp_path.chmod(0o700)
    authority = tmp_path/'model-authority'; authority.mkdir(mode=0o700)
    values={tmp_path/'run.json':{'controller_unit':UNIT,'model_authority_binding':'a'*64},
            authority/'binding.json':{'binding':'a'*64},
            authority/'requests.json':{'v':1,'binding':'a'*64,'remaining':0},
            authority/'revoked.json':{'persisted':True}}
    for path,value in values.items():
        path.write_text(json.dumps(value));path.chmod(0o600)
    return authority


def test_valid_revocation_is_read_only(tmp_path):
    authority=setup(tmp_path)
    before={p:p.read_bytes() for p in [tmp_path/'run.json',*authority.iterdir()]}
    assert VERIFY(tmp_path,controller_unit=UNIT,model_uid=os.geteuid()) is True
    assert before=={p:p.read_bytes() for p in before}


@pytest.mark.parametrize('fault',['missing-marker','marker-only','wrong-binding','old-controller',
    'boolean-zero','false-marker','shared-ledger','shared-directory','symlink','hardlink','fifo','oversize','wrong-owner'])
def test_unproven_revocation_denied(tmp_path,fault):
    authority=setup(tmp_path);path=authority/'requests.json';uid=os.geteuid()
    def patch(target,changes):
        data=json.loads(target.read_text());data.update(changes);target.write_text(json.dumps(data))
    if fault=='missing-marker':(authority/'revoked.json').unlink()
    elif fault=='marker-only':patch(path,{'remaining':5})
    elif fault=='wrong-binding':patch(path,{'binding':'b'*64})
    elif fault=='old-controller':patch(tmp_path/'run.json',{'controller_unit':UNIT.replace('a'*32,'b'*32)})
    elif fault=='boolean-zero':patch(path,{'remaining':False})
    elif fault=='false-marker':patch(authority/'revoked.json',{'persisted':False})
    elif fault=='shared-ledger':path.chmod(0o644)
    elif fault=='shared-directory':authority.chmod(0o755)
    elif fault=='symlink':
        original=authority/'original';path.rename(original);path.symlink_to(original)
    elif fault=='hardlink':os.link(path,authority/'alias')
    elif fault=='fifo':path.unlink();os.mkfifo(path,0o600)
    elif fault=='oversize':path.write_text(' '*4097)
    elif fault=='wrong-owner':uid+=1
    with pytest.raises(RuntimeError,match='Persistent model revocation not established'):
        VERIFY(tmp_path,controller_unit=UNIT,model_uid=uid)

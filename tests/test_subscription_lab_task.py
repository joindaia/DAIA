import hashlib
import json
from pathlib import Path
import runpy
import pytest

load = runpy.run_path(str(Path(__file__).parents[1]/'scripts/subscription_lab_task.py'))['load_task']


def test_frozen_task_and_legacy(tmp_path):
    assert load(tmp_path,{})['source']['path']=='src/version_check.py'
    fixture=Path(__file__).parent/'fixtures/subscription-development/outcome-summary.json'
    task=json.loads(fixture.read_text())
    document={k:task[k] for k in ('objective','baseline_commit','source')}
    raw=json.dumps(document).encode();path=tmp_path/'task.json';path.write_bytes(raw)
    config={'task_sha256':hashlib.sha256(raw).hexdigest()}
    assert load(tmp_path,config)==document
    with pytest.raises(ValueError,match='Unbound'):load(tmp_path,{})
    path.write_bytes(raw+b' ')
    with pytest.raises(ValueError,match='digest'):load(tmp_path,config)


def test_task_is_accepted_by_real_coordinator(tmp_path):
    from daia.service import Coordinator
    from daia.store import Store
    task=json.loads((Path(__file__).parent/'fixtures/subscription-development/outcome-summary.json').read_text())
    document={k:task[k] for k in ('objective','baseline_commit','source')}
    coordinator=Coordinator(Store(str(tmp_path/'network.sqlite3')))
    result=coordinator.admit_evidence(document)
    assert result

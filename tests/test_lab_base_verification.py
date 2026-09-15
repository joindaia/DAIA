from pathlib import Path
import runpy
from types import SimpleNamespace
import pytest

scope=runpy.run_path(str(Path(__file__).parents[1]/'scripts/verify_lab_base_image.py'))
verify=scope['verify']


@pytest.mark.parametrize('case',['bad_signature','duplicate','changed_pin','oversize'])
def test_verifier_refuses_before_opening_image(tmp_path,monkeypatch,case):
    manifest=tmp_path/'sums';signature=tmp_path/'sig';signature.write_bytes(b'synthetic')
    line=scope['PIN']+' *'+scope['IMAGE']+'\n'
    manifest.write_text(line)
    calls=[]
    def signature_result(*args,**kwargs):
        calls.append(True)
        return SimpleNamespace(returncode=1 if case=='bad_signature' else 0)
    monkeypatch.setattr(scope['subprocess'],'run',signature_result)
    if case=='duplicate': manifest.write_text(line+line)
    elif case=='changed_pin': manifest.write_text('0'*64+' *'+scope['IMAGE']+'\n')
    elif case=='oversize': manifest.write_bytes(b'x'*(128*1024+1))
    with pytest.raises(ValueError,match={'bad_signature':'signature rejected',
        'duplicate':'checksum required','changed_pin':'checksum required',
        'oversize':'too large'}[case]):
        verify(tmp_path/'absent.img',manifest,signature)
    assert len(calls)==(0 if case=='oversize' else 1)

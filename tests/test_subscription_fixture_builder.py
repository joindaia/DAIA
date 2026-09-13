"""Preparation refuses unapproved binary bytes before making output."""
from pathlib import Path
import runpy
import pytest

prepare = runpy.run_path(str(Path(__file__).parents[1] /
    'scripts/prepare_subscription_fixture.py'))['prepare']


def test_bad_native_pin_never_runs_builder(tmp_path, monkeypatch):
    native = tmp_path / 'native'; native.mkdir()
    (native / 'codex').write_bytes(b'not the approved original client')
    def forbidden(*a, **k):
        raise AssertionError('No child process permitted')
    monkeypatch.setattr('subprocess.run', forbidden)
    with pytest.raises(ValueError, match='pin mismatch'):
        prepare(tmp_path / 'template', native, tmp_path / 'out', '/unused', 'a' * 64)
    assert not (tmp_path / 'out').exists()


def test_bad_base_digest_refused_before_inputs(tmp_path):
    with pytest.raises(ValueError, match='base hash'):
        prepare('/missing', '/missing', tmp_path / 'out', '/unused', 'latest')
    assert not (tmp_path / 'out').exists()


def test_prepared_guest_uses_approved_model(tmp_path, monkeypatch):
    import ast
    import hashlib
    import json
    import tomllib
    from types import SimpleNamespace
    native = tmp_path/'native'; native.mkdir()
    for name in ('codex', 'bwrap'):
        (native/name).write_bytes(b'test binary')
    pins = {'codex': '56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da',
            'bwrap': '52231e1caf55bcbc667b269f49c63599a6f7db4767ae6a039580d0ff853db712'}
    monkeypatch.setattr(hashlib, 'file_digest', lambda stream, _: SimpleNamespace(hexdigest=lambda: pins[Path(stream.name).name]))
    def build(argv, **kwargs):
        Path(argv[argv.index('-output')+1]).write_bytes(b'test iso')
    monkeypatch.setattr('subprocess.run', build)
    template=tmp_path/'request.json';template.write_text(json.dumps({'model':'gpt-5.6-sol'}))
    output=tmp_path/'prepared'
    config=prepare(template,native,output,'fake-builder','a'*64)
    assert config['model']=='gpt-5.6-sol'
    cloud=json.loads((output/'user-data').read_text().split('\n',1)[1])
    code=next(f['content'] for f in cloud['write_files'] if f['path']=='/tmp/probe.py')
    configs=[n.value for n in ast.walk(ast.parse(code)) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('model = ')]
    assert len(configs)==1
    assert tomllib.loads(configs[0])['model']=='gpt-5.6-sol'
    assert config['seed_sha256']==hashlib.sha256(b'test iso').hexdigest()
    template.write_text(json.dumps({'model':'bad"\nsetting=true'}))
    with pytest.raises(ValueError,match='model identifier'):
        prepare(template,native,tmp_path/'invalid','fake-builder','a'*64)
    assert not (tmp_path/'invalid').exists()

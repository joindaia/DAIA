from pathlib import Path
import runpy
from types import SimpleNamespace
import pytest

scope = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/plan_fresh_host_packages.py'))
parse = scope['parse_plan']
LINE = "'https://archive.example/pkg.deb' pkg_1_amd64.deb 123 SHA256:" + 'a' * 64


def test_exact_download_manifest():
    result = parse('APT summary\n' + LINE)
    assert result == [{'url': 'https://archive.example/pkg.deb', 'filename': 'pkg_1_amd64.deb', 'bytes': 123, 'sha256': 'a'*64}]


@pytest.mark.parametrize('text', ['', LINE+'\n'+LINE, LINE.replace('SHA256:', 'MD5Sum:'),
    LINE.replace('pkg_1_amd64.deb', '../pkg.deb'), LINE.replace(' 123 ', ' 0 '),
    LINE.replace('https://archive', 'https://secret@archive')])
def test_invalid_acquisition_record_rejected(text):
    with pytest.raises(ValueError): parse(text)


def test_planner_uses_empty_state_and_never_installs(tmp_path, monkeypatch):
    def apt(argv, **kwargs):
        assert '--print-uris' in argv and '--download-only' in argv
        assert 'Acquire::ForceHash=sha256' in argv
        status = next(x.split('=', 1)[1] for x in argv if x.startswith('Dir::State::status='))
        assert Path(status).read_bytes() == b''
        assert kwargs['check'] is True
        return SimpleNamespace(stdout=LINE)
    monkeypatch.setattr(scope['subprocess'], 'run', apt)
    result = scope['plan'](tmp_path / 'new')
    assert result == {'packages': 1, 'download_bytes': 123, 'downloaded': False, 'installed': False}
    with pytest.raises(FileExistsError): scope['plan'](tmp_path / 'new')

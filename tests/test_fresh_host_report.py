"""Replay the observed cloud-init prefix against the actual probe runner."""
import ast
import json
from pathlib import Path
import subprocess
import sys
import textwrap
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).parents[1]


def runner_source():
    tree = ast.parse((ROOT / 'scripts/probe_fresh_host_ram.py').read_text())
    return textwrap.dedent(next(ast.literal_eval(n.value) for n in ast.walk(tree)
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'runner' for t in n.targets)))


@pytest.mark.parametrize('case', ['prefixed', 'bare', 'duplicate', 'wrong_nonce', 'bad_prefix'])
def test_report_and_cleanup(tmp_path, monkeypatch, capsys, case):
    nonce = 'a' * 32
    marker = 'DAIA_FRESH_HOST ' + json.dumps({'nonce': nonce})
    line = '[   14.217959] cloud-init[932]: ' + marker
    if case == 'bare': line = marker
    if case == 'duplicate': line += '\n' + line
    if case == 'bad_prefix': line = 'arbitrary ' + line
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['probe', '/base', '/seed', 'b'*32 if case == 'wrong_nonce' else nonce])
    def fake_run(argv, **kwargs):
        if argv[0] == 'qemu-img':
            Path('guest.qcow2').write_bytes(b'fixture')
        else:
            assert argv[argv.index('-nic') + 1] == 'none'
            Path('serial.txt').write_text(line)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, 'run', fake_run)
    if case in ('prefixed', 'bare'):
        exec(compile(runner_source(), '<runner>', 'exec'), {})
        assert json.loads(capsys.readouterr().out)['nonce'] == nonce
    else:
        with pytest.raises(AssertionError):
            exec(compile(runner_source(), '<runner>', 'exec'), {})
    assert not Path('guest.qcow2').exists()

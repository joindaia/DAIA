"""Offline assembly: pin copied bytes and never reuse existing output."""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import pytest

prepare = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/prepare_kvm_bundle.py'))['prepare']


def test_reproducible_bundle_and_rejected_inputs(tmp_path):
    base, seed = tmp_path / 'base', tmp_path / 'seed'
    base.write_bytes(b'synthetic base'); seed.write_bytes(b'synthetic seed')
    args = dict(base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),
                seed_sha256=hashlib.sha256(seed.read_bytes()).hexdigest(), nonce='a' * 32)
    first, second = tmp_path / 'first', tmp_path / 'second'
    one = prepare(base, seed, first, **args)
    assert prepare(base, seed, second, **args) == one
    assert len(one) == 8
    assert 'seconds=150, max_bytes=256 * 1024' in (first / 'bridge.py').read_text()
    for name in ('model-bridge.py', 'research-bridge.py'):
        assert 'relay(connection, 0, 1)' in (first / name).read_text()
    manifest = json.loads((first / 'network-config.json').read_text())
    assert manifest['base_sha256'] == args['base_sha256']
    for name, expected in manifest['bridge_sha256'].items():
        assert one[name] == expected
    assert '/run/daia-lab/model.sock' in (first / 'model-bridge.py').read_text()
    assert '/run/daia-research/gateway.sock' in (first / 'research-bridge.py').read_text()
    assert all(p.stat().st_mode & 0o222 == 0 for p in first.iterdir())
    with pytest.raises(FileExistsError):
        prepare(base, seed, first, **args)
    bad = tmp_path / 'bad'
    with pytest.raises(ValueError, match='digest mismatch'):
        prepare(base, seed, bad, **{**args, 'seed_sha256': '0' * 64})
    assert not bad.exists()
    link = tmp_path / 'linked'; link.symlink_to(base)
    with pytest.raises(ValueError, match='regular input'):
        prepare(link, seed, bad, **args)
    assert not bad.exists()


@pytest.mark.skipif(sys.platform != 'linux', reason='diagnostic wrapper uses Linux-only /tmp service layout')
def test_failed_launch_exports_only_bounded_private_diagnostics(tmp_path):
    import subprocess
    bundle = tmp_path / 'bundle'; bundle.mkdir()
    (bundle / 'launcher.py').write_text("from pathlib import Path\nassert not any(Path.cwd().iterdir()), 'Working directory must remain empty'\nPath('serial.txt').write_bytes(b'DAIA_NATIVE_FAILURE synthetic error\\n'+b'x'*20000)\nraise ValueError('Guest correlation result missing')\n")
    work = tmp_path / 'work'; work.mkdir()
    wrapper = Path(__file__).parents[1] / 'scripts/run_kvm_lab_report.py'
    result = subprocess.run([sys.executable, '-I', str(wrapper), '--bundle', str(bundle)],
                            cwd=work, capture_output=True, text=True, timeout=5)
    assert result.returncode == 1 and not result.stderr
    report = json.loads(result.stdout)
    assert report['ok'] is False
    assert 'DAIA_NATIVE_FAILURE synthetic error' in report['untrusted_failure_context']
    assert len(report['untrusted_failure_context'].encode()) <= 8192
    assert report['untrusted_diagnostics']['serial.txt'] == 'x' * 4096
    assert report['untrusted_diagnostics']['stderr.txt'] == ''
    assert 'Guest correlation result missing' in report['untrusted_diagnostics']['launcher-error.txt']
    assert len(report['untrusted_diagnostics']['launcher-error.txt'].encode()) <= 4096


def test_native_report_starts_a_new_serial_line():
    import ast
    import io
    from contextlib import nullcontext
    source = Path(__file__).parents[1] / 'scripts/prepare_native_delivery_fixture.py'
    tree = ast.parse(source.read_text())
    snippets = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
                and isinstance(n.value, str) and "out.write(" in n.value
                and 'DAIA_BOOT_RESULT' in n.value]
    assert len(snippets) == 1
    output = io.StringIO(); output.write('unterminated console output')
    result = {'nonce': 'a' * 32}
    scope = {'items': [{'type': 'mcp_tool_call'}] * 3, 'model_result': result,
             'json': json, 'open': lambda *a: nullcontext(output)}
    exec(compile(snippets[0], 'trusted-report-writer', 'exec'), scope)
    markers = [json.loads(line[17:]) for line in output.getvalue().splitlines()
               if line.startswith('DAIA_BOOT_RESULT ')]
    assert len(markers) == 1 and markers[0]['nonce'] == 'a' * 32


def test_missing_research_result_remains_failure_with_private_stage(tmp_path):
    import ast
    import io
    from contextlib import nullcontext
    from types import SimpleNamespace
    fixture = Path(__file__).parent / 'fixtures/subscription-development'
    tree = ast.parse((fixture / 'probe.py').read_text())
    guard = next(n for n in tree.body if isinstance(n, ast.Try)
                 and "model_result['research']" in ast.unparse(n))
    start = next(i for i, n in enumerate(tree.body) if isinstance(n, ast.Assign)
                 and ast.unparse(n).startswith("root = pathlib.Path('/work/research')"))
    end = next(i for i, n in enumerate(tree.body) if isinstance(n, ast.If)
               and "result['native_exit']" in ast.unparse(n.test))
    # Only trusted diagnostic statements with synthetic inputs; no guest startup,
    # candidate source, network requests or downloaded package code is executed.
    code = compile(ast.Module(body=tree.body[start:end] + [guard], type_ignores=[]),
                   'trusted-research-check', 'exec')
    output = io.StringIO()
    root = tmp_path / 'research'; root.mkdir()
    (root / 'failure.json').write_text('{"stage":"documentation","error_type":"OSError"}')
    scope = {'json': json, 'model_result': {}, 'r': SimpleNamespace(returncode=0),
             'pathlib': SimpleNamespace(Path=lambda p: tmp_path / p.removeprefix('/work/')),
             'open': lambda *a: nullcontext(output)}
    with pytest.raises(FileNotFoundError):
        exec(code, scope)
    record = json.loads(output.getvalue().strip().removeprefix('DAIA_NATIVE_FAILURE '))
    assert record['stage'] == 'research_result'
    assert record['research_failure']['stage'] == 'documentation'
    assert record['files']['result.json'] is False
    assert 'research' not in scope['model_result']
    (root / 'result.json').write_text('{"dependency_import_and_checks":true}')
    output.seek(0); output.truncate()
    exec(code, scope)
    assert scope['model_result']['research']['dependency_import_and_checks'] is True
    assert not output.getvalue()
    output.seek(0); output.truncate()
    scope.update(result={'native_exit': 1, 'turn_completed': False}, events=[])
    scope['r'] = SimpleNamespace(returncode=1, stderr='')
    native_failure = compile(ast.Module(body=tree.body[start:end+1], type_ignores=[]),
                             'trusted-native-failure-check', 'exec')
    with pytest.raises(RuntimeError, match='native development failed'):
        exec(native_failure, scope)
    first = output.getvalue().strip().splitlines()[0]
    assert json.loads(first.removeprefix('DAIA_NATIVE_FAILURE '))['stage'] == 'research_result'


def test_research_exception_record_excludes_exception_message(tmp_path):
    import ast
    from types import SimpleNamespace
    fixture = Path(__file__).parent / 'fixtures/subscription-development/research.py'
    function = next(n for n in ast.parse(fixture.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'report_failure')
    calls = []
    scope = {'root': tmp_path, 'stage': 'package_download', 'json': json,
             'sys': SimpleNamespace(__excepthook__=lambda *args: calls.append(args))}
    exec(compile(ast.Module(body=[function], type_ignores=[]), 'trusted-error-recorder', 'exec'), scope)
    error = RuntimeError('synthetic sensitive exception text')
    scope['report_failure'](RuntimeError, error, None)
    assert json.loads((tmp_path / 'failure.json').read_text()) == {
        'stage': 'package_download', 'error_type': 'RuntimeError'}
    assert calls == [(RuntimeError, error, None)]

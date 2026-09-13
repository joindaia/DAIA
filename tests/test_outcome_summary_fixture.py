"""Exercise the prepared task boundary without credentials, VM or model calls."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
from types import SimpleNamespace


def test_prepared_task_and_bounded_failure_diagnostic(tmp_path, monkeypatch):
    module = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/prepare_outcome_summary_fixture.py'))
    source = tmp_path / 'source'
    source.mkdir()
    code = '''
original = 'def newer(a, b): return a > b\\n'
tests = 'from version_check import newer\\n'
prompt = 'Complete this assigned development task using native DAIA MCP tools.'
nonce = 'original-nonce'
try:
    pass
except Exception:
    with open('/dev/ttyS0', 'w') as out:
        out.write('DAIA_NATIVE_FAILURE ')
'''
    (source / 'user-data').write_text('#cloud-config\n' + json.dumps({'write_files': [{'path': '/tmp/probe.py', 'content': code}]}))
    (source / 'config.json').write_text(json.dumps({'nonce': 'original-nonce'}))
    for name in ('network-config', 'probe.py'):
        (source / name).write_text('fixture')
    output = tmp_path / 'prepared'
    def build_iso(argv, **kwargs):
        Path(argv[argv.index('-output') + 1]).write_bytes(b'synthetic-iso')
    monkeypatch.setattr(module['subprocess'], 'run', build_iso)
    config = module['prepare'](source, output, tmp_path, 'fake-iso-builder')
    assert config['retry_receipt'] is True
    assert config['nonce'] != 'original-nonce'
    for filename, key in [('task.json', 'task_sha256'), ('seed.iso', 'seed_sha256')]:
        assert hashlib.sha256((output / filename).read_bytes()).hexdigest() == config[key]
    cloud = json.loads((output / 'user-data').read_text().split('\n', 1)[1])
    tree = ast.parse(cloud['write_files'][0]['content'])
    diagnostic = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'diagnostic' for t in n.targets))
    # Evaluate only the trusted diagnostic expression, never supplied task code.
    items = [{'type': 'command_execution', 'command': 'x' * 300,
              'aggregated_output': 'y' * 500, 'exit_code': 127}] * 4
    items.append({'type': 'command_execution', 'command': 'success', 'exit_code': 0})
    result = eval(compile(ast.Expression(diagnostic), '<diagnostic>', 'eval'),
                  {'r': SimpleNamespace(returncode=1), 'items': items})
    assert result['failed_commands'] == [['x' * 100, 'y' * 160]] * 2
    assert len(result['items']) == 5
    assert 'success' not in json.dumps(result)

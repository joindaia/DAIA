"""Prepare the second development task from an approved native-delivery fixture.

Installer-only: transforms repository fixture code, never executes task code.
The controller must bind the exported task document before issuing the assignment.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import uuid


COMPANION_PIN = '3e85d67471825f73d02ff5f7e047ca1f6ca8caa3f59e4c6e8d9ca6ca7302cb45'


def companion_inputs(native):
    native = Path(native)
    paths = [native / 'codex', native / 'bwrap']
    companion = native / 'codex-code-mode-host'
    present = companion.exists() or companion.is_symlink()
    digest = None
    if present:
        if companion.is_symlink() or not companion.is_file():
            raise ValueError('Pinned companion regular file required')
        with companion.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != COMPANION_PIN:
            raise ValueError('Native companion pin mismatch')
        paths.append(companion)
    return paths, present, digest


def validate_source_companion(source_config, present, digest):
    expected_present = source_config.get('companion_present', False)
    expected_digest = source_config.get('companion_sha256')
    if (type(expected_present) is not bool or expected_present != present
            or expected_digest != (COMPANION_PIN if present else None)):
        raise ValueError('Derived fixture companion metadata mismatch')


def prepare(source, output, native, iso_builder):
    source, output, native = Path(source), Path(output), Path(native)
    native_inputs, companion_present, companion_sha256 = companion_inputs(native)
    source_config = json.loads((source / 'config.json').read_text())
    validate_source_companion(source_config, companion_present, companion_sha256)
    task = json.loads((Path(__file__).parents[1] /
        'tests/fixtures/subscription-development/outcome-summary.json').read_text())
    source_text = task['source']['text']
    packet = {'source_digest': hashlib.sha256(source_text.encode()).hexdigest(),
              'line': 1, 'finding': 'Operator outcome aggregation is not implemented.',
              'reproduction_outline': 'Run the supplied summary tests against the original and updated module.',
              'suggested_change': 'REPLACE WITH ONLY THE NEW summarize_outcomes FUNCTION, MAXIMUM 1200 CHARACTERS'}
    prompt = ('Complete this DAIA assignment using native MCP tools. Call heartbeat once. '
              'Use one terminal invocation to run python3 /work/research.py, read /work/task.py '
              'and /work/test_task.py, implement the requirement, run the unchanged tests and '
              'print only the added function. The existing module is supplied here so you can design the addition before the terminal call: ' + source_text + '\nRequirement: ' + task['objective'] +
              ' Then call submit_result with verdict candidate and artifact equal to a JSON '
              'string of this packet, replacing suggested_change with ONLY the appended function (maximum 1200 characters), not the original module. Append the function without editing existing source: ' +
              json.dumps(packet) + ' The helper handles one lost receipt internally. '
              'Do not submit twice after a successful receipt. Finish after the receipt. '
              'Maximum six model requests. No additional heartbeat. Do not invoke MCP via shell.')
    cloud = json.loads((source/'user-data').read_text().split('\n', 1)[1])
    entry = next(f for f in cloud['write_files'] if f['path']=='/tmp/probe.py')
    config = json.loads((source/'config.json').read_text())
    nonce = uuid.uuid4().hex
    replaced = set()

    class TaskLiterals(ast.NodeTransformer):
        def visit_Constant(self, node):
            value = node.value
            if not isinstance(value, str): return node
            if value == 'def newer(a, b): return a > b\n':
                value = source_text; replaced.add('source')
            elif value.startswith('from version_check import newer\n'):
                value = task['tests']; replaced.add('tests')
            elif value.startswith('Complete this assigned development task using native DAIA MCP tools.'):
                value = prompt; replaced.add('prompt')
            elif value == '/work/version_check.py': value = '/work/task.py'
            elif value == '/work/test_version.py': value = '/work/test_task.py'
            elif value == config['nonce']: value = nonce; replaced.add('nonce')
            return ast.copy_location(ast.Constant(value=value), node)

    code = ast.unparse(TaskLiterals().visit(ast.parse(entry['content']))) + '\n'
    if replaced != {'source','tests','prompt','nonce'}:
        raise ValueError('Expected native task fixture required')
    code=code.replace("assert len(mcp_items) >= 3", "assert len(mcp_items) >= 2")
    # Private diagnostics only: retain bounded tool outcomes on failed turns.
    failure_write = "with open('/dev/ttyS0', 'w') as out:\n        out.write('DAIA_NATIVE_FAILURE "
    if code.count(failure_write) != 1:
        raise ValueError('Expected native failure diagnostic')
    details = "diagnostic = {'native_exit': r.returncode, 'failed_commands': [[str(i.get('command',''))[:100], str(i.get('aggregated_output',''))[-160:]] for i in items if i.get('type') == 'command_execution' and i.get('exit_code') not in (None, 0)][:2], 'items': [[{'command_execution':'command','mcp_tool_call':'mcp','agent_message':'message'}.get(i.get('type'),'other'), str(i.get('tool',''))[-48:], i.get('exit_code') if type(i.get('exit_code')) is int else None] for i in items[-10:]]}\n    "
    code = code.replace(failure_write, details + failure_write)
    compile(code, 'outcome-summary-guest', 'exec')  # Syntax only.
    entry['content'] = code
    output.mkdir()
    (output/'user-data').write_text('#cloud-config\n'+json.dumps(cloud))
    (output/'meta-data').write_text(json.dumps({'instance-id':'daia-summary-'+nonce,'local-hostname':'daia-summary'}))
    (output/'network-config').write_bytes((source/'network-config').read_bytes())
    (output/'probe.py').write_bytes((source/'probe.py').read_bytes())
    document = {k:task[k] for k in ('objective','baseline_commit','source')}
    raw = json.dumps(document, sort_keys=True).encode()
    (output/'task.json').write_bytes(raw)
    subprocess.run([str(iso_builder),'-quiet','-output',str(output/'seed.iso'),
        '-volid','CIDATA','-joliet','-rock',
        *[str(output/name) for name in ('user-data','meta-data','network-config')],
        *[str(path) for path in native_inputs]],check=True)
    config=source_config
    config.update(retry_receipt=True,nonce=nonce,companion_present=companion_present,companion_sha256=companion_sha256,task_sha256=hashlib.sha256(raw).hexdigest(),
                  seed_sha256=hashlib.sha256((output/'seed.iso').read_bytes()).hexdigest())
    (output/'config.json').write_text(json.dumps(config))
    return config


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','output','native','iso-builder'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.source,args.output,args.native,args.iso_builder)))

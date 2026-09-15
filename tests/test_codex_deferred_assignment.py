import json
import runpy
from pathlib import Path

import pytest


scope = runpy.run_path(str(Path(__file__).parents[1] /
                           'scripts/probe_codex_deferred_assignment.py'))


def test_custom_tool_turn_uses_responses_custom_tool_schema():
    events = scope['custom_tool_events']().decode().split('\n\n')
    payloads = [json.loads(part.split('data: ', 1)[1]) for part in events if part]
    assert payloads[2]['type'] == 'response.custom_tool_call_input.delta'
    assert payloads[2]['delta'] == scope['CODE']
    item = payloads[4]['item']
    assert item['type'] == 'custom_tool_call'
    assert item['name'] == 'exec'
    assert item['namespace'] == 'functions'
    assert item['input'] == scope['CODE']


def test_deferred_catalog_requires_both_assignment_capabilities():
    output = json.dumps({'name': 'mcp__daia_assignment__heartbeat'})
    assert scope['extract_assignment_names'](output) == ['mcp__daia_assignment__heartbeat']
    assert scope['deferred_output']({'input': [
        {'type': 'custom_tool_call_output', 'output': output}
    ]}) == output
    assert not {'mcp__daia_assignment__heartbeat',
                 'mcp__daia_assignment__submit_result'}.issubset(
                     scope['extract_assignment_names'](output))


def test_model_and_binary_boundaries_are_explicit(tmp_path):
    with pytest.raises(ValueError, match='Pinned original Codex binary'):
        scope['validate_binary'](tmp_path / 'fake')
    assert scope['model_identifier']('gpt-6-astra') == 'gpt-6-astra'
    assert scope['EXPECTED_NAMES'] == {
        'mcp__daia_assignment__heartbeat', 'mcp__daia_assignment__submit_result'}

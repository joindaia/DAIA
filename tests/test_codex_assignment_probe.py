import runpy
from pathlib import Path

import pytest


scope = runpy.run_path(str(Path(__file__).parents[1] /
                           'scripts/probe_codex_assignment_tools.py'))


def test_missing_native_tools_fail_closed_with_protocol_error():
    with pytest.raises(RuntimeError, match='enumerable top-level tools missing'):
        scope['assignment_tools']({'input': [{'type': 'additional_tools'}]})


def test_native_probe_model_selection_is_validated_and_compatible():
    parser = scope['build_parser']()
    assert parser.parse_args([]).model == 'gpt-5.3-codex-spark'
    assert parser.parse_args(['--model', 'gpt-5.6-luna']).model == 'gpt-5.6-luna'
    assert parser.parse_args(['--model', 'gpt-5.6-unknown']).model == 'gpt-5.6-unknown'
    assert parser.parse_args(['--model', 'gpt-6-astra']).model == 'gpt-6-astra'
    with pytest.raises(SystemExit):
        parser.parse_args(['--model', 'bad;provider'])
    with pytest.raises(SystemExit):
        parser.parse_args(['--model', 'bad model'])

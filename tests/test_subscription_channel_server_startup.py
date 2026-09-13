import http.client
import json
from pathlib import Path
import runpy
import sys
import types

import pytest


def test_startup_preserves_selected_model_before_service_loop(tmp_path, monkeypatch):
    runtime = tmp_path / 'runtime'
    (runtime / 'daia-lab' / 'templates').mkdir(parents=True)
    (runtime / 'daia-authority').mkdir()
    (runtime / 'daia-authority' / 'binding.json').write_text(json.dumps({'binding': 'test'}))
    (runtime / 'daia-lab' / 'templates' / 'model-template.json').write_text(
        json.dumps({'model': 'gpt-5.6-luna', 'input': [], 'tools': []}))
    (runtime / 'daia-lab' / 'subscription-auth.json').write_text(
        json.dumps({'address': '127.0.0.1', 'access_token': 'fake', 'account_id': 'fake'}))

    real_path = Path

    def mapped_path(value):
        value = str(value)
        for source, target in (
            ('/run/daia-lab', runtime / 'daia-lab'),
            ('/var/lib/daia-lab', runtime / 'daia-lab'),
            ('/run/daia-authority', runtime / 'daia-authority'),
        ):
            if value == source or value.startswith(source + '/'):
                return real_path(target / value[len(source):].lstrip('/'))
        return real_path(value)

    captured = {}
    stop = type('StartupStop', (Exception,), {})

    model_request = types.ModuleType('daia.model_request')
    model_request.Denied = ValueError
    model_request.RequestGate = object
    model_request._decode = lambda raw: json.loads(raw)
    model_request._history = lambda items: None
    model_channel = types.ModuleType('daia.model_channel')

    class AssignmentModelChannel:
        def __init__(self, approved_template, forward, **kwargs):
            captured['template'] = json.loads(approved_template)
            raise stop

    model_channel.AssignmentModelChannel = AssignmentModelChannel
    codex_https = types.ModuleType('daia.codex_https')
    codex_https.CodexHTTPSUpstream = lambda *args, **kwargs: object()
    model_response = types.ModuleType('daia.model_response')
    model_response.completed_output = lambda output: []
    daia = types.ModuleType('daia')
    daia.__path__ = []
    monkeypatch.setitem(sys.modules, 'daia', daia)
    for module in (model_request, model_channel, codex_https, model_response):
        monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr('pathlib.Path', mapped_path)
    monkeypatch.setattr(sys, 'argv', ['probe_subscription_channel_server.py'])

    original_getresponse = http.client.HTTPConnection.getresponse
    monkeypatch.setattr(http.client.HTTPConnection, 'getresponse', original_getresponse)
    with pytest.raises(stop):
        runpy.run_path(str(Path(__file__).parents[1] / 'scripts/probe_subscription_channel_server.py'))

    assert captured['template']['model'] == 'gpt-5.6-luna'
    assert not (runtime / 'daia-lab' / 'subscription-auth.json').exists()

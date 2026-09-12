"""Response-fixture checks; these do not establish live gateway isolation."""
import io
import json
from pathlib import Path
import runpy
import urllib.request

import pytest


@pytest.mark.parametrize('case', [
    'json', 'sse', 'wrong-id-json', 'wrong-id-sse', 'pagination',
    'missing-error', 'false-error', 'empty-init', 'missing-session',
    'changed-session', 'extra-content', 'init-error',
])
def test_probe_rejects_ambiguous_gateway_evidence(monkeypatch, case):
    probe = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/probe_static_mcp.py'))
    monkeypatch.setenv('MCP_GATEWAY_URL', 'http://mcp-gateway.docker.internal/mcp')
    request_ids = []

    def respond(req, timeout):
        message = json.loads(req.data)
        if 'id' not in message:
            response = io.BytesIO(b'')
            response.headers = {}
            return response
        request_ids.append(message['id'])
        reply = {'jsonrpc': '2.0', 'id': message['id'], 'result': {}}
        if message['method'] == 'initialize':
            reply['result'] = {'protocolVersion': '2025-03-26'}
            if case == 'init-error':
                del reply['result']
                reply['error'] = {'code': -32603, 'message': 'failed'}
        if message['method'] == 'tools/list':
            reply['result'] = {'tools': [{'name': 'code-mode'}, {'name': 'mcp-exec'}]}
            if case == 'pagination':
                reply['result']['nextCursor'] = 'more'
        elif message['method'] == 'tools/call':
            name = message['params']['name']
            args = message['params']['arguments']
            if name.startswith('mcp-') and name != 'mcp-exec':
                del reply['result']
                reply['error'] = {'code': -32602, 'message': f'unknown tool "{name}"'}
            else:
                if name == 'mcp-exec':
                    text = f'Tool "{args["name"]}" not found in gateway.'
                else:
                    text = ('error: tools not found in gateway: ' + args['tools'][0]
                            if args['tools'] else 'error: at least one tool name is required')
                reply['result'] = {'isError': True, 'content': [{'type': 'text', 'text': text}]}
                if name == 'mcp-exec' and case == 'extra-content':
                    reply['result']['content'].append({'type': 'text', 'text': 'extra'})
                if name == 'code-mode' and case == 'missing-error':
                    del reply['result']['isError']
                if name == 'code-mode' and case == 'false-error':
                    reply['result']['isError'] = False
        if case.startswith('wrong-id'):
            reply['id'] = 999
        raw = json.dumps(reply).encode()
        if case.endswith('sse'):
            raw = b'data: ' + raw + b'\n\n'
        if case == 'empty-init' and message['method'] == 'initialize':
            raw = b''
        response = io.BytesIO(raw)
        response.headers = ({'Mcp-Session-Id': 'fixture-session'}
                            if message['method'] == 'initialize' and case != 'missing-session' else {})
        if message['method'] != 'initialize' and case == 'changed-session':
            response.headers['Mcp-Session-Id'] = 'other-session'
        return response

    monkeypatch.setattr(urllib.request, 'urlopen', respond)
    if case in ('json', 'sse'):
        probe['main']()
        assert len(request_ids) == len(set(request_ids))
    else:
        with pytest.raises(RuntimeError):
            probe['main']()

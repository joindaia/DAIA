"""Run inside a disposable guest with a fixed MCP set containing an empty fixture.

No task code, server registration, credentials or arbitrary JavaScript are sent.
This tests missing management tools, not the isolation of code-mode execution.
"""
import itertools
import json
import os
import urllib.request


def main():
    url = os.environ.get('MCP_GATEWAY_URL')
    if url != 'http://mcp-gateway.docker.internal/mcp':
        raise RuntimeError('Run only inside the prepared Docker guest')
    headers = {'Content-Type': 'application/json',
               'Accept': 'application/json, text/event-stream'}

    def request(message):
        req = urllib.request.Request(url, data=json.dumps(message).encode(), headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            session = response.headers.get('Mcp-Session-Id')
            if message.get('method') == 'initialize':
                if not session:
                    raise RuntimeError('Gateway initialization did not establish a session')
                headers['Mcp-Session-Id'] = session
            elif session and session != headers.get('Mcp-Session-Id'):
                raise RuntimeError('Gateway changed the initialized session')
            raw = response.read(65537)
            if len(raw) > 65536:
                raise RuntimeError('Gateway response exceeds probe bound')
        if not raw:
            if 'id' in message:
                raise RuntimeError('Missing JSON-RPC response')
            return {}
        try:
            reply = json.loads(raw)
        except ValueError:
            messages = [json.loads(line[6:]) for line in raw.decode().splitlines()
                        if line.startswith('data: ')]
            matches = [item for item in messages if item.get('id') == message.get('id')]
            if len(matches) != 1:
                raise RuntimeError('Expected exactly one matching MCP response')
            reply = matches[0]
        if (not isinstance(reply, dict) or reply.get('jsonrpc') != '2.0'
                or type(reply.get('id')) is not int or reply['id'] != message.get('id')
                or (('result' in reply) == ('error' in reply))):
            raise RuntimeError('Invalid or uncorrelated JSON-RPC response')
        return reply

    ids = itertools.count(3)

    def call(name, arguments):
        return request({'jsonrpc': '2.0', 'id': next(ids), 'method': 'tools/call',
                        'params': {'name': name, 'arguments': arguments}})

    initialized = request({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
        'protocolVersion': '2025-03-26', 'capabilities': {},
        'clientInfo': {'name': 'daia-static-mcp-probe', 'version': '1'}}})
    if initialized.get('result', {}).get('protocolVersion') != '2025-03-26':
        raise RuntimeError('Gateway initialization did not negotiate the requested protocol')
    request({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    listing = request({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
    names = {item['name'] for item in listing['result']['tools']}
    if listing['result'].get('nextCursor') or names != {'code-mode', 'mcp-exec'}:
        raise RuntimeError('Unexpected tool surface; use a fixed empty fixture')
    for name in ('mcp-add', 'mcp-config-set', 'mcp-find'):
        result = call(name, {})
        if result.get('error') != {'code': -32602, 'message': f'unknown tool "{name}"'}:
            raise RuntimeError('Direct management-tool denial not established')
        result = call('mcp-exec', {'name': name, 'arguments': {}}).get('result', {})
        expected = [{'type': 'text', 'text': f'Tool "{name}" not found in gateway.'}]
        if result.get('isError') is not True or result.get('content') != expected:
            raise RuntimeError('Indirect management-tool denial not established')
    for tools, expected in (
            ([], 'error: at least one tool name is required'),
            (['mcp-add'], 'error: tools not found in gateway: mcp-add'),
            (['mcp-exec'], 'error: tools not found in gateway: mcp-exec'),
            (['code-mode'], 'error: tools not found in gateway: code-mode')):
        result = call('code-mode', {'tools': tools}).get('result', {})
        if (result.get('isError') is not True
                or result.get('content') != [{'type': 'text', 'text': expected}]):
            raise RuntimeError('Code-mode exclusion not established')
    print('PASS: fixed-set listing and ten gateway denial probes')


if __name__ == '__main__':
    main()

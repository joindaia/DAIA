"""Real restricted MCP exchange from a Linux namespace; relay is a test fixture."""
import asyncio
import json
import os
from pathlib import Path
import selectors
import socket
import subprocess
import sys
import time

import pytest

pytest.importorskip('mcp')
from daia.contributor import Contributor
from daia.isolation import sandbox_command
from daia.mcp_server import build_mcp_app
from daia.service import Coordinator
from daia.store import Store
from test_assignment_host import approve
from test_contributor import direct, invite_file
from test_mcp import running_server

pytestmark = pytest.mark.skipif(
    sys.platform != 'linux' or os.environ.get('DAIA_RUN_ISOLATION_TESTS') != '1',
    reason='Explicit real namespace integration test',
)


def test_isolated_process_submits_only_pinned_work(tmp_path):
    service = Coordinator(Store(str(tmp_path / 'network.sqlite3')))
    service.seed()
    snapshot = tmp_path / 'input'; snapshot.mkdir()
    private = tmp_path / 'helper'; private.mkdir(mode=0o700)
    endpoint = private / 'assignment.sock'
    with running_server(build_mcp_app(service)) as url:
        invite = invite_file(private, service, url)
        host = direct(Contributor(invite, minutes=5), service)
        lease = asyncio.run(host.perform('request_work'))
        before = (host.state['key'], host.state['used'], host.state['deadline'])
        policy = private / 'approval.json'
        policy.write_text(json.dumps(approve(host, lease, ['read_input', 'heartbeat', 'submit_result'])))
        policy.chmod(0o600)
        program = '''import json,pathlib,socket
assert not pathlib.Path(INVITE).exists()
assert not pathlib.Path(STATE).exists()
assert not pathlib.Path('/run/approval.json').exists()
s=socket.socket(socket.AF_UNIX);s.settimeout(5);s.connect('/run/daia-assignment.sock')
stream=s.makefile('rwb', buffering=0)
def send(value): stream.write(json.dumps(value).encode()+b'\\n')
def rpc(number,method,params):
 send({'jsonrpc':'2.0','id':number,'method':method,'params':params})
 while True:
  line=stream.readline(65537)
  assert line.endswith(b'\\n') and len(line)<=65536
  response=json.loads(line)
  if response.get('id')==number:
   assert 'error' not in response,response
   return response['result']
rpc(1,'initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'isolated-probe','version':'1'}})
send({'jsonrpc':'2.0','method':'notifications/initialized'})
assert {t['name'] for t in rpc(2,'tools/list',{})['tools']}=={'heartbeat','submit_result'}
assert rpc(3,'tools/call',{'name':'request_work','arguments':{}})['isError']
assert not rpc(4,'tools/call',{'name':'heartbeat','arguments':{}}).get('isError',False)
result=rpc(5,'tools/call',{'name':'submit_result','arguments':{'artifact':'{"factors":[101,103]}','verdict':'candidate'}})
assert not result.get('isError',False)
assert json.loads(result['content'][0]['text'])['status']=='in_review'
pathlib.Path('/work/result.txt').write_text('submission completed')
print('isolated restricted MCP submission passed')
'''.replace('INVITE', repr(str(invite))).replace('STATE', repr(str(host.path)))
        with socket.socket(socket.AF_UNIX) as listener:
            listener.bind(str(endpoint)); endpoint.chmod(0o600)
            listener.listen(1); listener.settimeout(5)
            helper = subprocess.Popen(
                [sys.executable, '-B', '-m', 'daia.contributor', '--invite', str(invite),
                 '--job-authority', str(policy), '--assignment', lease['assignment_id']],
                env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')},
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            )
            worker = None
            try:
                worker = subprocess.Popen(
                    sandbox_command(snapshot, ['/usr/bin/python3', '-c', program], assignment_socket=endpoint),
                    env={'PATH': '/usr/bin:/bin'}, stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True,
                )
                connection, _ = listener.accept()
                # Known small fixture messages only; not a production relay.
                with connection, selectors.DefaultSelector() as streams:
                    streams.register(connection, selectors.EVENT_READ, 'worker')
                    streams.register(helper.stdout, selectors.EVENT_READ, 'helper')
                    deadline = time.monotonic() + 15
                    transferred = 0
                    while worker.poll() is None and time.monotonic() < deadline:
                        events = streams.select(.1)
                        disconnected = False
                        for key, _ in events:
                            chunk = os.read(key.fileobj.fileno(), 8192)
                            if not chunk:
                                disconnected = True
                                break
                            transferred += len(chunk)
                            assert transferred <= 256 * 1024
                            if key.data == 'worker':
                                helper.stdin.write(chunk); helper.stdin.flush()
                            else:
                                connection.sendall(chunk)
                        if disconnected: break
                stdout, stderr = worker.communicate(timeout=5)
                assert worker.returncode == 0, stderr.decode()
                assert stdout.strip() == b'isolated restricted MCP submission passed'
            finally:
                if worker is not None:
                    if worker.poll() is None: worker.kill()
                    worker.communicate(timeout=5)
                helper.terminate()
                try: helper.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    helper.kill(); helper.communicate(timeout=5)
        saved = json.loads(host.path.read_text())
        assert (saved['key'], saved['used'], saved['deadline']) == before
        assert service.metrics()['results'] == 1

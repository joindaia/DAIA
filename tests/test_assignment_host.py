"""An assignment-only interface must not follow later work or expand consent."""
import asyncio
import copy

import pytest

from daia.contributor import Contributor, build_assignment_server
from test_contributor import direct, invite_file


def approve(host, lease, capabilities):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from daia.crypto import public_hex
    from daia.job_authorization import authorize_job
    key = Ed25519PrivateKey.generate()
    approval = authorize_job(lease, key=key, agent_id=host.agent,
                             capabilities=capabilities, expires=lease['hard_deadline'],
                             now=int(host.clock()))
    return {'public_key': public_hex(key), 'capabilities': capabilities,
            'jobs': {lease['job_id']: approval}}


def test_scope_refuses_other_assignment_and_recovery_substitution(network, tmp_path):
    service, now = network
    service.seed()
    host = direct(Contributor(invite_file(tmp_path, service), clock=service.clock), service)

    async def exercise():
        lease = await host.perform('request_work')
        assignment = lease['assignment_id']
        before = copy.deepcopy(host.state)
        original_remote = host.remote
        async def unexpected_remote(*args, **kwargs):
            raise AssertionError('Out-of-scope call reached coordinator')
        host.remote = unexpected_remote
        for operation, scope in [('request_work', assignment), ('submit_result', '0' * 32),
                                 ('stop_contributing', assignment), ('heartbeat', '')]:
            with pytest.raises(ValueError, match='scope'):
                await host.perform(operation, assignment_id=scope)
        assert host.state == before
        host.remote = original_remote
        async def substituted_recovery():
            host.state['lease']['assignment_id'] = 'f' * 32
            return {}
        host.recover = substituted_recovery
        with pytest.raises(ValueError, match='scope'):
            await host.perform('submit_result', assignment_id=assignment,
                               artifact='{"factors":[101,103]}', verdict='candidate')
        assert service.metrics()['results'] == 0
    asyncio.run(exercise())


def test_scoped_pending_retry_survives_restart_and_expiry(network, tmp_path):
    service, now = network
    service.seed()
    path = invite_file(tmp_path, service)

    async def exercise():
        host = direct(Contributor(path, minutes=1, clock=service.clock), service)
        lease = await host.perform('request_work')
        assignment = lease['assignment_id']
        authority = approve(host, lease, ['read_input', 'heartbeat', 'submit_result'])
        host.job_authority = authority
        original = (host.state['key'], host.state['used'], host.state['deadline'])
        direct(host, service, lose='submit_result')
        with pytest.raises(ValueError, match='response loss'):
            await host.perform('submit_result', assignment_id=assignment,
                               artifact='{"factors":[101,103]}', verdict='candidate')
        now[0] += 301
        restarted = direct(Contributor(path, clock=service.clock, job_authority=authority), service)
        receipt = await restarted.perform('submit_result', assignment_id=assignment,
                                          artifact='{"factors":[101,103]}', verdict='candidate')
        assert receipt['status'] == 'already_recorded'
        assert (restarted.state['key'], restarted.state['used'], restarted.state['deadline']) == original
        assert service.metrics()['results'] == 1
        with pytest.raises(ValueError, match='scope'):
            await restarted.perform('heartbeat', assignment_id=assignment)
    asyncio.run(exercise())


def test_assignment_server_exposes_no_claim_identity_or_consent_tools(network, tmp_path):
    service, _ = network
    service.seed()
    host = direct(Contributor(invite_file(tmp_path, service), clock=service.clock), service)

    async def exercise():
        assignment = (await host.perform('request_work'))['assignment_id']
        with pytest.raises(ValueError, match='authority'):
            build_assignment_server(host, assignment)
        host.job_authority = {'public_key': 'unused', 'capabilities': [], 'jobs': {}}
        server = build_assignment_server(host, assignment)
        tools = await server.list_tools()
        assert {tool.name for tool in tools} == {'heartbeat', 'submit_result'}
        assert await server.list_resources() == []
        assert await server.list_resource_templates() == []
        for uri in ('file:///etc/passwd', 'file:///state/helper.json', 'https://example.org'):
            with pytest.raises(Exception, match='Unknown resource'):
                await server.read_resource(uri)
        for tool in tools:
            assert set(tool.input_schema.get('properties', {})) <= {'artifact', 'verdict'}
    asyncio.run(exercise())


def test_assignment_stdio_uses_existing_identity_and_signed_job(tmp_path):
    import json
    from pathlib import Path
    import sys
    import time
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from daia.crypto import public_hex
    from daia.job_authorization import authorize_job
    from daia.mcp_server import build_mcp_app
    from daia.service import Coordinator
    from daia.store import Store
    from test_mcp import running_server, call

    service = Coordinator(Store(str(tmp_path / 'network.sqlite3')))
    service.seed()
    async def exercise(path):
        host = direct(Contributor(path, minutes=5), service)
        lease = await host.perform('request_work')
        before = (host.state['key'], host.state['used'], host.state['deadline'])
        key = Ed25519PrivateKey.generate()
        capabilities = ['read_input', 'heartbeat', 'submit_result']
        approval = authorize_job(lease, key=key, agent_id=host.agent,
                                 capabilities=capabilities, expires=lease['hard_deadline'],
                                 now=int(time.time()))
        policy = tmp_path / 'authority.json'
        policy.write_text(json.dumps({'public_key': public_hex(key), 'capabilities': capabilities,
                                     'jobs': {lease['job_id']: approval}}))
        policy.chmod(0o600)
        parameters = StdioServerParameters(command=sys.executable, args=[
            '-B', '-m', 'daia.contributor', '--invite', str(path),
            '--job-authority', str(policy), '--assignment', lease['assignment_id']],
            env={'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')})
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                assert {t.name for t in (await session.list_tools()).tools} == {'heartbeat', 'submit_result'}
                refused = await session.call_tool('request_work', {})
                assert refused.is_error
                await call(session, 'heartbeat')
                receipt = await call(session, 'submit_result', artifact='{"factors":[101,103]}', verdict='candidate')
                assert receipt['status'] == 'in_review'
        saved = json.loads(path.with_suffix('.contributor.json').read_text())
        assert (saved['key'], saved['used'], saved['deadline']) == before
        assert service.metrics()['results'] == 1
    with running_server(build_mcp_app(service)) as url:
        asyncio.run(exercise(invite_file(tmp_path, service, url)))


@pytest.mark.parametrize('assignment', ['', 'invalid'])
def test_cli_invalid_scope_never_starts_general_host(tmp_path, assignment):
    import os
    from pathlib import Path
    import subprocess
    import sys
    invite = tmp_path / 'unused-invite.json'
    result = subprocess.run(
        [sys.executable, '-B', '-m', 'daia.contributor', '--invite', str(invite),
         '--assignment', assignment],
        env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')},
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 2
    assert '--assignment requires an exact assignment ID' in result.stderr
    assert not invite.with_suffix('.contributor.json').exists()


def test_scoped_operations_require_explicit_signed_capabilities(network, tmp_path):
    service, _ = network
    service.seed()
    host = direct(Contributor(invite_file(tmp_path, service), clock=service.clock), service)
    async def exercise():
        lease = await host.perform('request_work')
        host.job_authority = approve(host, lease, ['read_input'])
        for operation in ['heartbeat', 'submit_result']:
            with pytest.raises(ValueError, match='capability'):
                await host.perform(operation, assignment_id=lease['assignment_id'],
                                   artifact='{"factors":[101,103]}', verdict='candidate')
        assert host.state['pending'] is None
        assert service.metrics()['results'] == 0
    asyncio.run(exercise())


def test_source_evidence_receipt_loss_over_http_survives_helper_restart(network, tmp_path):
    """Transport preparation for the combined worker; no model or VM is used."""
    import json
    import time
    from daia.mcp_server import build_mcp_app
    from test_mcp import running_server
    from test_evidence import document, packet

    service, now = network
    now[0] = int(time.time())
    service.admit_evidence(document())

    async def exercise(url):
        path = invite_file(tmp_path, service, url, max_jobs=1)
        host = Contributor(path, minutes=1, clock=service.clock)
        lease = await host.perform('request_work')
        assignment = lease['assignment_id']
        authority = approve(host, lease, ['read_input', 'heartbeat', 'submit_result'])
        host.job_authority = authority
        original = (host.state['key'], host.state['used'], host.state['deadline'])
        artifact = packet(lease)
        remote = host.remote
        async def lose_receipt(name, **args):
            result = await remote(name, **args)
            if name == 'submit_result':
                raise ValueError('Simulated response loss after committed operation')
            return result
        host.remote = lose_receipt
        await host.perform('heartbeat', assignment_id=assignment)
        with pytest.raises(ValueError, match='response loss'):
            await host.perform('submit_result', assignment_id=assignment,
                               artifact=artifact, verdict='candidate')
        assert service.metrics()['results'] == 1
        now[0] += 301
        restarted = Contributor(path, clock=service.clock, job_authority=authority)
        changed = json.loads(artifact); changed['suggested_change'] = 'Substituted patch'
        with pytest.raises(ValueError, match='exact pending'):
            await restarted.perform('submit_result', assignment_id=assignment,
                                    artifact=json.dumps(changed), verdict='candidate')
        receipt = await restarted.perform('submit_result', assignment_id=assignment,
                                         artifact=artifact, verdict='candidate')
        assert receipt['status'] == 'already_recorded'
        assert service.metrics()['results'] == 1
        assert service.metrics()['promoted'] == 0
        assert (restarted.state['key'], restarted.state['used'], restarted.state['deadline']) == original
        with pytest.raises(ValueError, match='scope'):
            await restarted.perform('request_work', assignment_id=assignment)

    with running_server(build_mcp_app(service)) as url:
        asyncio.run(exercise(url))


@pytest.mark.parametrize('recovery', ['library', 'controller'])
def test_source_evidence_receipt_survives_forced_helper_process_death(network, tmp_path, recovery):
    """Kill the real helper after HTTP commit, before local receipt persistence."""
    import json
    import os
    from pathlib import Path
    import subprocess
    import sys
    import time
    from daia.mcp_server import build_mcp_app
    from test_mcp import running_server
    from test_evidence import document, packet

    service, now = network
    now[0] = int(time.time())
    service.admit_evidence(document())
    ready = tmp_path / 'committed'
    graceful = tmp_path / 'graceful'
    config = tmp_path / 'child.json'
    child = tmp_path / 'child.py'
    child.write_text("""import asyncio, atexit, json, pathlib, sys
from daia.contributor import Contributor
c=json.loads(pathlib.Path(sys.argv[1]).read_text())
atexit.register(lambda: pathlib.Path(c['graceful']).touch())
host=Contributor(c['invite'],job_authority=c['authority'])
remote=host.remote
async def pause_after_commit(name,**args):
 result=await remote(name,**args)
 if name=='submit_result':
  pathlib.Path(c['ready']).touch()
  await asyncio.Event().wait()
 return result
host.remote=pause_after_commit
asyncio.run(host.perform('submit_result',assignment_id=c['assignment'],artifact=c['artifact'],verdict='candidate'))
""")

    async def exercise(url):
        path = invite_file(tmp_path, service, url, max_jobs=1)
        host = Contributor(path, minutes=1, clock=service.clock)
        lease = await host.perform('request_work')
        assignment = lease['assignment_id']
        authority = approve(host, lease, ['read_input', 'heartbeat', 'submit_result'])
        original = {k: host.state[k] for k in ('key', 'used', 'deadline', 'max_jobs')}
        artifact = packet(lease)
        config.write_text(json.dumps(dict(invite=str(path), authority=authority,
                                         assignment=assignment, artifact=artifact,
                                         ready=str(ready), graceful=str(graceful))))
        config.chmod(0o600)
        process = subprocess.Popen([sys.executable, str(child), str(config)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')})
        try:
            deadline = time.monotonic() + 15
            while not ready.exists() and time.monotonic() < deadline:
                assert process.poll() is None, 'helper exited before committed marker'
                await asyncio.sleep(.02)
            assert ready.exists(), 'helper did not reach committed response'
            assert service.metrics()['results'] == 1
            saved = json.loads(host.path.read_text())
            assert saved['pending']['artifact'] == artifact
            assert saved['receipt'] is None
            process.kill()
            process.wait(timeout=5)
            assert process.returncode != 0 and not graceful.exists()
            if os.name == 'posix':
                assert process.returncode == -9
        finally:
            if process.poll() is None:
                process.kill(); process.wait(timeout=5)

        now[0] += 301
        restored = Contributor(path, clock=service.clock, job_authority=authority)
        with pytest.raises(ValueError, match='exact pending'):
            await restored.perform('submit_result', assignment_id=assignment,
                                   artifact=artifact + ' ', verdict='candidate')
        if recovery == 'controller':
            authority_path = tmp_path / 'authority.json'
            authority_path.write_text(json.dumps(authority))
            command = [sys.executable, '-m', 'daia.contributor', '--invite', str(path),
                       '--job-authority', str(authority_path), '--recover-pending']
            environment = {**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')}
            before_refusal = path.with_suffix('.contributor.json').read_bytes()
            wrong = subprocess.run(command + ['f' * 32], env=environment,
                                   capture_output=True, text=True, timeout=15)
            assert wrong.returncode == 1 and not wrong.stdout
            assert path.with_suffix('.contributor.json').read_bytes() == before_refusal
            completed = subprocess.run(command + [assignment], env=environment,
                                       capture_output=True, text=True, timeout=15)
            assert completed.returncode == 0, completed.stderr
            assert completed.stdout == 'DAIA pending receipt recovered.\n'
            restored = Contributor(path, clock=service.clock, job_authority=authority)
            receipt = restored.state['receipt']
            # Repeating the controller action does not start a generic MCP host
            # or claim work once pending state has been cleared.
            again_cli = subprocess.run(command + [assignment], env=environment,
                                       capture_output=True, text=True, timeout=15)
            assert again_cli.returncode == 1 and not again_cli.stdout
        else:
            receipt = await restored.perform('submit_result', assignment_id=assignment,
                                             artifact=artifact, verdict='candidate')
        assert receipt['status'] == 'already_recorded'
        assert service.metrics()['results'] == 1
        assert {k: restored.state[k] for k in original} == original
        assert restored.state['pending'] is None
        assert restored.state['receipt']['receipt_hash'] == receipt['receipt_hash']
        again = Contributor(path, clock=service.clock, job_authority=authority)
        assert again.state['receipt'] == restored.state['receipt']
        assert again.state['pending'] is None
        with pytest.raises(ValueError, match='scope'):
            await again.perform('request_work', assignment_id=assignment)

    with running_server(build_mcp_app(service)) as url:
        asyncio.run(exercise(url))


def test_pending_save_failure_never_allows_unsaved_retry(network, tmp_path, monkeypatch):
    service, _ = network
    service.seed()
    host = direct(Contributor(invite_file(tmp_path, service), clock=service.clock), service)

    async def exercise():
        lease = await host.perform('request_work')
        assignment = lease['assignment_id']
        host.job_authority = approve(host, lease, ['read_input', 'heartbeat', 'submit_result'])
        save = host.save
        remote = host.remote
        attempts = []
        async def observe(name, **arguments):
            if name == 'submit_result':
                import json
                assert json.loads(host.path.read_text())['pending'] == host.state['pending']
                attempts.append(name)
            result = await remote(name, **arguments)
            if name == 'contribution_status' and host.state['pending']:
                # Recovery ignores an unsolicited different assignment so the
                # pending receipt can still be retried; that path does not save.
                result = copy.deepcopy(result)
                result['lease'] = {**lease, 'assignment_id': 'f' * 32}
            return result
        host.remote = observe
        def disk_failure():
            if host.state['pending']:
                raise OSError('injected storage failure')
            save()
        monkeypatch.setattr(host, 'save', disk_failure)
        for _ in range(2):
            with pytest.raises(OSError, match='storage failure'):
                await host.perform('submit_result', assignment_id=assignment,
                                   artifact='{"factors":[101,103]}', verdict='candidate')
            assert not attempts
            assert service.metrics()['results'] == 0
        monkeypatch.setattr(host, 'save', save)
        await host.perform('submit_result', assignment_id=assignment,
                           artifact='{"factors":[101,103]}', verdict='candidate')
        assert len(attempts) == 1
        assert service.metrics()['results'] == 1
        assert host.state['pending'] is None
    asyncio.run(exercise())

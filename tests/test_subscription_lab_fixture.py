"""Actual HTTP claim and delivery, with no in-process remote replacement."""
import asyncio
from pathlib import Path
import runpy
from daia.contributor import Contributor
from daia.mcp_server import build_mcp_app
from daia.service import Coordinator
from daia.store import Store

fixture = runpy.run_path(str(Path(__file__).parents[1]/'scripts/subscription_lab_fixture.py'))


def test_real_lab_mcp_path_preserves_binding_and_exact_retry(tmp_path):
    service = Coordinator(Store(str(tmp_path/'state.sqlite3')))
    service.seed()
    with fixture['running_server'](build_mcp_app(service)) as url:
        host = Contributor(fixture['invite_file'](tmp_path,service,url),minutes=5)
        async def run():
            lease = await host.perform('request_work')
            before = {k:host.state[k] for k in ('key','used','deadline','max_jobs')}
            host.job_authority = fixture['approve'](host,lease,['read_input','heartbeat','submit_result'])
            args = dict(assignment_id=lease['assignment_id'],artifact='{"factors":[101,103]}',verdict='candidate')
            await host.perform('heartbeat',assignment_id=lease['assignment_id'])
            remote=host.remote
            async def lose(name, **kwargs):
                result=await remote(name,**kwargs)
                if name=='submit_result': raise ValueError('lost lab response')
                return result
            host.remote=lose
            try: await host.perform('submit_result',**args)
            except ValueError as error: assert str(error)=='lost lab response'
            else: raise AssertionError('Expected simulated lost response')
            host.remote=remote
            receipt=await host.perform('submit_result',**args)
            assert receipt['status']=='already_recorded'
            assert {k:host.state[k] for k in before}==before
            assert service.metrics()['results']==1
        asyncio.run(run())

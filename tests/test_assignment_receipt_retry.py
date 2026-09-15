import asyncio
import copy
import json
import pytest
from daia.contributor import Contributor, submit_assignment_result
from test_contributor import direct, invite_file
from test_assignment_host import approve


@pytest.mark.parametrize('losses,enabled,expected_calls',[(1,True,2),(2,True,2),(1,False,1)])
def test_exact_retry_has_no_new_authority(network,tmp_path,losses,enabled,expected_calls):
    service,_=network;service.seed()
    host=direct(Contributor(invite_file(tmp_path,service),clock=service.clock),service)
    async def exercise():
        lease=await host.perform('request_work')
        host.job_authority=approve(host,lease,['read_input','submit_result'])
        before={k:host.state[k] for k in ('key','used','deadline','max_jobs')}
        remote=host.remote;submissions=[]
        async def lossy(name,**args):
            result=await remote(name,**args)
            if name=='submit_result':
                submissions.append(copy.deepcopy(args))
                if len(submissions)<=losses:raise ValueError('Response lost')
            return result
        host.remote=lossy
        call=submit_assignment_result(host,lease['assignment_id'],'{"factors":[101,103]}','candidate',retry_receipt=enabled)
        if enabled and losses==1:
            assert (await call)['status']=='already_recorded'
            assert host.state['pending'] is None
        else:
            with pytest.raises(ValueError,match='Response lost'):await call
            assert host.state['pending']
        assert len(submissions)==expected_calls
        assert all(x==submissions[0] for x in submissions)
        assert service.metrics()['results']==1
        assert {k:host.state[k] for k in before}==before
    asyncio.run(exercise())


def test_one_mcp_call_recovers_lost_receipt(network,tmp_path):
    from daia.contributor import build_assignment_server
    service,_=network;service.seed()
    host=direct(Contributor(invite_file(tmp_path,service),clock=service.clock),service)
    async def exercise():
        lease=await host.perform('request_work')
        host.job_authority=approve(host,lease,['read_input','submit_result'])
        remote=host.remote;calls=[]
        async def lossy(name,**args):
            result=await remote(name,**args)
            if name=='submit_result':
                calls.append(copy.deepcopy(args))
                if len(calls)==1:raise ValueError('Response lost')
            return result
        host.remote=lossy
        server=build_assignment_server(host,lease['assignment_id'],retry_receipt=True)
        result=await server.call_tool('submit_result',{'artifact':'{"factors":[101,103]}','verdict':'candidate'})
        data=result.model_dump(by_alias=True)
        assert data.get('isError') is not True
        receipt=data.get('structuredContent') or json.loads(data['content'][0]['text'])
        assert receipt['status']=='already_recorded'
        assert len(calls)==2 and calls[0]==calls[1]
        assert host.state['pending'] is None and service.metrics()['results']==1
    asyncio.run(exercise())

"""Diagnosis isolation and context boundaries, not a claim of natural-language accuracy."""
import json
from copy import deepcopy

import httpx
import pytest
from fastapi.testclient import TestClient

from app.approach import approach_diagnostic
from app.domain import Turn, initial_state, resolve
from app.intent import intent_context, intent_schema
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.providers import MockProvider, build_context
from app.relationship import relationship_plan
from app.settings import Settings
from app.world import load_world


def diagnosis(text, labels=None):
    return {'labels':labels or ['emotional_appeal','cooperation'],'evidence':text,'reason':'현재 발언의 사정 설명과 협력 의사.'}


def model_transport(requests, diagnostic):
    def handle(request):
        payload=json.loads(request.content)
        requests.append(payload)
        title=payload['format']['title']
        if title=='IntentProposal':
            text=json.loads(payload['messages'][-1]['content'])['text']
            value={'kind':'conversation','action':None,'target':None,'evidence':''}
            if any('approach' in branch['properties'] for branch in payload['format']['anyOf']):
                if diagnostic is not None:
                    value['approach']=diagnostic(text)
        elif title=='DialogueReview':
            value={'consistent':True,'issues':[]}
        else:
            value={k:v['const'] for k,v in payload['format']['properties'].items() if 'const' in v}
            value['dialogue']='급한 마음은 이해합니다. 공개된 범위에서 사정을 듣겠습니다.'
        return httpx.Response(200,json={'done':True,'message':{'role':'assistant','content':json.dumps(value)}})
    return httpx.MockTransport(handle)


@pytest.mark.parametrize('diagnostic,status',[
    (diagnosis,'reported'),
    (lambda text:diagnosis(text,['unclear']),'reported'),
    (lambda text:diagnosis(text,['bargaining','pressure','evasion']),'reported'),
    (lambda text:diagnosis('다른 발언'),'invalid'),
    (lambda text:{**diagnosis(text),'trust_delta':100},'invalid'),
    (lambda text:diagnosis(text,['unknown']),'invalid'),
    (lambda text:diagnosis(text,['pressure','pressure']),'invalid'),
    (None,'unavailable'),
])
def test_diagnostics_do_not_change_actions_numbers_or_saved_memory(tmp_path,diagnostic,status):
    seen=[]
    provider=OllamaProvider(Settings(),transport=model_transport(seen,diagnostic))
    with TestClient(create_app(tmp_path/'game.sqlite3',provider=provider,settings=Settings(dev_mode=True))) as client:
        before=client.post('/api/games').json()
        response=client.post(f"/api/branches/{before['id']}/chat",json={'text':'사정을 말씀드리고 싶어요.','mode':'free','revision':0})
        assert response.status_code==200,response.text
        after=response.json()
        assert after['debug']['approach']['status']==status
        assert len(seen)==3
        assert after['generation']['llm_calls']==3
        assert after['debug']['decision']['action']=='speak'
        for key in ('trust','guard','events','ended','memories','progress','config','world_settings','relationship_rules','confidential'):
            assert after['state'][key]==before['state'][key]
        assert 'approach' not in json.dumps(after['state'])
        assert 'approach' not in json.dumps(after['debug']['provider_input'])
        assert 'approach' not in json.dumps(seen[1:])
        assert 'approach' not in client.get(f"/api/branches/{before['id']}").text
        assert after['state']['config']['judgment_guidelines'][0] in seen[1]['messages'][0]['content']


@pytest.mark.parametrize('dev_mode,mode,calls',[(False,'free',3),(True,'direct',2)])
def test_no_extra_calls_or_diagnosis_outside_dev_free_mode(tmp_path,dev_mode,mode,calls):
    seen=[]
    provider=OllamaProvider(Settings(),transport=model_transport(seen,diagnosis))
    with TestClient(create_app(tmp_path/'game.sqlite3',provider=provider,settings=Settings(dev_mode=dev_mode))) as client:
        before=client.post('/api/games').json()
        response=client.post(f"/api/branches/{before['id']}/chat",json={'text':'안녕하세요.','mode':mode,'revision':0})
        assert response.status_code==200,response.text
        body=response.json()
        assert len(seen)==calls
        assert 'approach_diagnostics' not in json.dumps(seen,ensure_ascii=False)
        assert 'approach' not in body.get('debug',{})


def test_source_and_approach_schema_coexist_without_new_secret_disclosure():
    state=initial_state()
    turn=Turn(text='계몽의 서',revision=0)
    from app.domain import advance_state
    plan=relationship_plan(state,turn,resolve(state,'speak'))
    state=advance_state(state,turn,plan['verdict'],plan)
    context=intent_context(state,'출처는 밝히지 않겠습니다.',diagnostics=True)
    schema=intent_schema(context)
    for branch in schema['anyOf']:
        assert 'source_answer' in branch['required'] and 'approach' in branch['required']
    assert set(schema['$defs'])=={'SourceAnswer','ApproachDiagnosis'}
    assert '계몽의 서' not in json.dumps(context,ensure_ascii=False)
    provider=OllamaProvider(Settings())
    provider.structured_stage=lambda messages,schema,validator:provider.stage_payload(messages,schema)
    assert provider.interpret(context)['options']['num_ctx']==8192


@pytest.mark.parametrize('interaction,source',[
    ({'kind':'conversation','focus':None},False),
    ({'kind':'clarify','reason':'ambiguous_target'},False),
    ({'kind':'conversation','focus':'sealed','reason':'hypothetical'},False),
    ({'kind':'direct'},False),
    ({'kind':'conversation'},True),
])
def test_judgment_criteria_and_context_reach_dialogue_routes(interaction,source):
    state=initial_state()
    state['config']['player_only']='PLAYER_PRIVATE_014'
    state['config']['author_notes']='AUTHOR_PRIVATE_014'
    state['messages'].extend([
        {'role':'user','content':'아버지의 기록을 찾는다고 말씀드렸어요.','action':'speak'},
        {'role':'assistant','content':'어떤 시기의 기록을 찾으십니까?','consistency':{'status':'passed'}},
    ])
    turn=Turn(text='확실한 부분부터 말씀드릴게요.',revision=0)
    if source:
        turn=Turn(text='계몽의 서',revision=0)
        plan=relationship_plan(state,turn,resolve(state,'speak'))
        context=build_context(state,turn,plan['verdict'],plan)
    else:
        context=build_context(state,turn,resolve(state,'speak'))
    context['interaction']=interaction
    payload=OllamaProvider(Settings()).payload(context)
    packed=json.dumps(payload,ensure_ascii=False)
    assert turn.text in packed
    assert '어떤 시기의 기록을 찾으십니까?' in packed
    assert state['config']['judgment_guidelines'][0] in packed
    assert 'PLAYER_PRIVATE_014' not in packed and 'AUTHOR_PRIVATE_014' not in packed
    assert 'serin_knows_location' not in packed
    for record in state['config']['public_records']:
        assert record['content'] not in packed


def test_restored_diagnostic_context_has_no_future_utterances_or_labels(tmp_path):
    class Recorder(MockProvider):
        def __init__(self):
            self.inputs=[]
        def interpret(self,context):
            self.inputs.append(deepcopy(context))
            return {**super().interpret(context),'approach':diagnosis(context['text'],['evasion'])}
    model=Recorder()
    with TestClient(create_app(tmp_path/'game.sqlite3',provider=model,settings=Settings(dev_mode=True))) as client:
        branch=client.post('/api/games').json()
        def send(branch,text):
            response=client.post(f"/api/branches/{branch['id']}/chat",json={'text':text,'mode':'free','revision':branch['revision']})
            assert response.status_code==200,response.text
            return response.json()
        first=send(branch,'이전 발언')
        future=send(first,'FUTURE_FAMILY_CLAIM_014')
        restored=client.post(f"/api/branches/{future['id']}/regress",json={'turn_number':1,'revision':future['revision']}).json()
        assert restored['state']==first['state']
        send(restored,'다시 말씀드릴게요.')
        packed=json.dumps(model.inputs[-1],ensure_ascii=False)
        assert 'FUTURE_FAMILY_CLAIM_014' not in packed
        assert 'evasion' not in packed
        assert '이전 발언' in packed


def test_old_world_does_not_gain_judgment_criteria_without_new_game(tmp_path):
    world=load_world()
    world.pop('judgment_guidelines')
    path=tmp_path/'world.json'
    path.write_text(json.dumps(world),encoding='utf-8')
    assert 'judgment_guidelines' not in load_world(path)
    old=initial_state(world=world)
    context=build_context(old,Turn(text='안녕하세요.',revision=0),resolve(old,'speak'))
    assert 'judgment_guidelines' not in context['instructions']
    assert approach_diagnostic(None,'안녕하세요.')['status']=='unavailable'

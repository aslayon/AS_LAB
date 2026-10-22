"""Deterministic state tests use controlled proposals, not claims about LLM accuracy."""
import json
from copy import deepcopy
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.confidential import detects_title, initial_confidential, SourceAnswer
from app.domain import Proposal, Turn, initial_state, resolve, advance_state
from app.intent import intent_context, intent_schema
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.providers import MockProvider, build_context
from app.relationship import load_rules, relationship_plan
from app.settings import Settings
from app.store import Store, encode


class ControlledSource(MockProvider):
    def __init__(self):
        self.answer = None
        self.action, self.target = None, None
        self.inputs, self.drafts, self.reviews = [], [], []
    def interpret(self, context):
        self.inputs.append(deepcopy(context))
        result = {'kind':'attempt' if self.action else 'conversation', 'action':self.action,
                  'target':self.target, 'evidence':context['text'] if self.action else ''}
        if self.answer is not None:
            result['source_answer'] = deepcopy(self.answer)
        return result
    def propose(self, context):
        self.drafts.append(deepcopy(context))
        return super().propose(context)
    def review(self, context, proposal):
        self.reviews.append(deepcopy(context))
        return super().review(context, proposal)


def step(client, branch, text, provider, answer=None, action=None, target=None):
    provider.answer = {'type':answer, 'evidence':text if answer != 'uncertain' else ''} if answer else None
    provider.action, provider.target = action, target
    response = client.post(f"/api/branches/{branch['id']}/chat", json={'text':text, 'revision':branch['revision'], 'mode':'free'})
    assert response.status_code == 200, response.text
    return response.json()


def transact(state, text, kind=None, action='speak', evidence=None):
    turn = Turn(text=text, action=action, revision=0)
    raw = {'type':kind, 'evidence':text if evidence is None else evidence} if kind else None
    plan = relationship_plan(state, turn, resolve(state, action), raw)
    updated = advance_state(state, turn, plan['verdict'], plan)
    updated['messages'] += [{'role':'user','content':text,'action':action}, {'role':'assistant','content':'대역'}]
    return updated, plan


@pytest.mark.parametrize('text,expected', [
    ('안녕하세요.',False), ('중요한 기록이 있나요?',False), ('계몽의 책',False), ('계몽 의 서',False),
    ('계몽의 서를 아세요?',True), ('계몽의서',True), ('계몽의 서는 모르는데요',True),
    ('친구가 "계몽의 서"라고 했어요.',True),
])
def test_exact_title_recognition_is_not_access_or_knowledge(text, expected):
    before = initial_state()
    after, plan = transact(before,text)
    assert detects_title(before,text) == expected
    assert after['guard'] == before['guard'] + (10 if expected else 0)
    assert after['trust'] == before['trust']
    assert after['confidential']['title_mentioned'] == expected
    for key in ('events','progress','ended','memories'):
        assert after[key] == before[key]
    assert before['confidential'] == initial_confidential()
    assert plan['source_result'] is not None if expected else plan['source_result'] is None


def test_repeat_and_disclosed_titles_have_no_extra_adjustment():
    state, _ = transact(initial_state(),'계몽의 서')
    for text in ['계몽의서', '"계몽의 서"?', '계몽의 서']:
        state, plan = transact(state,text,'evasion')  # Even a wrong classifier cannot punish a bare repeated title.
        assert state['guard'] == 30
        assert state['confidential']['rechecks'] == 0
    state['confidential']['source_status'] = 'closed'
    state,_ = transact(state,'계몽의 서는 모르겠어요.')
    assert state['guard'] == 30
    shown = initial_state();shown['confidential']['disclosed_by_serin'] = True
    shown,plan = transact(shown,'계몽의 서가 있나요?')
    assert shown['guard'] == 20 and plan['source_result'] is None
    assert shown['confidential']['source_status'] == 'idle'


def test_concrete_source_is_only_an_unverified_user_claim():
    state,_ = transact(initial_state(),'계몽의 서를 찾습니다.')
    text = '어제 시장에서 서점 주인 한 씨에게 제목을 들었습니다.'
    state,plan = transact(state,text,'concrete')
    assert state['confidential']['source_claims'] == [{'text':text,'status':'user_claim','verified':False}]
    assert state['confidential']['source_status'] == 'closed'
    assert (state['trust'],state['guard']) == (30,30)
    assert state['events']['access'] == 'sealed'
    for _ in range(3):
        state,_ = transact(state,'이제 다른 얘기를 하죠.','evasion')
    assert state['guard'] == 30 and not state['ended']


@pytest.mark.parametrize('first', ['vague','topic_change','evasion'])
def test_one_recheck_then_clear_evasion_once(first):
    state,_ = transact(initial_state(),'계몽의 서')
    state,plan = transact(state,'그냥 들었습니다.',first)
    assert state['guard'] == 30 and state['confidential']['rechecks'] == 1
    assert plan['source_result']['act'] == 'reask_source'
    state,plan = transact(state,'출처 얘기는 됐고 다른 이야기나 합시다.','evasion')
    assert state['guard'] == 35 and state['trust'] == 30
    assert state['confidential']['additional_guard_applied']
    assert state['confidential']['closing_reason'] == 'evasion'
    for _ in range(3):
        state,_ = transact(state,'비가 오네요.','evasion')
    assert state['guard'] == 35 and not state['ended']


@pytest.mark.parametrize('kind,evidence', [('uncertain',''),('refusal','입력에 없는 거절'),('concrete','입력에 없는 출처')])
def test_uncertain_or_ungrounded_interpretation_never_penalizes(kind,evidence):
    state,_ = transact(initial_state(),'계몽의 서')
    state,plan = transact(state,'무슨 뜻인지 모르겠어요.',kind,evidence=evidence)
    assert state['guard'] == 30
    assert state['confidential']['source_status'] == 'closed'
    assert state['confidential']['source_claims'] == []


def test_explicit_refusal_and_remaining_vagueness():
    state,_ = transact(initial_state(),'계몽의 서')
    state,_ = transact(state,'누구에게 들었는지는 말할 수 없습니다.','refusal')
    assert state['guard'] == 35 and state['confidential']['closing_reason'] == 'refusal'
    state,_ = transact(state,'또 말할 수 없습니다.','refusal')
    assert state['guard'] == 35
    vague,_ = transact(initial_state(),'계몽의 서')
    vague,_ = transact(vague,'어디선가 들었어요.','vague')
    vague,_ = transact(vague,'잘 기억 안 나요.','vague')
    assert vague['guard'] == 30 and vague['confidential']['source_status'] == 'closed'


def test_independent_action_plus_mention_and_refusal_sum_once():
    state,plan = transact(initial_state(),'계몽의 서를 찾는다. 봉인을 강제로 뜯는다.',action='force_access')
    assert plan['verdict']['guard_delta'] == 35
    assert (state['trust'],state['guard']) == (15,55)
    assert state['events']['forced_attempts'] == 1
    assert [r['rule'] for r in plan['audit']['rules']] == ['forced_access','secret_first_mention']
    state,plan = transact(state,'출처는 말 못 합니다. 봉인을 다시 강제로 뜯는다.','refusal',action='force_access')
    assert plan['verdict']['guard_delta'] == 30
    assert (state['trust'],state['guard']) == (0,85)
    assert state['ended']
    assert state['relationship_rule_counts']['forced_access'] == 2
    assert state['relationship_rule_counts']['secret_first_mention'] == 1
    # Existing ending takes priority; this feature does not keep asking after exit.
    left,plan = transact(initial_state(),'계몽의 서라는 말을 남기고 떠납니다.',action='leave')
    assert left['ended'] and left['confidential']['source_status'] == 'closed'
    assert plan['source_result']['act'] == 'source_closed'


def test_clamp_after_sum_not_per_rule():
    state = initial_state();state['guard'] = 90
    after,plan = transact(state,'계몽의 서. 봉인을 강제로 뜯는다.',action='force_access')
    assert after['guard'] == 100
    assert plan['audit']['proposed_delta']['guard_delta'] == 35
    assert plan['audit']['actual_delta']['guard'] == 10


def test_api_regression_restores_source_claims_counts_and_all_model_boundaries(tmp_path):
    provider = ControlledSource()
    with TestClient(create_app(tmp_path/'test.sqlite3',provider=provider,settings=Settings(dev_mode=True))) as client:
        base=client.post('/api/games').json()
        base=step(client,base,'안녕하세요.',provider)
        future=step(client,base,'계몽의 서를 아십니까?',provider)
        future=step(client,future,'어제 출처_CANARY_832에게 들었어요.',provider,'concrete')
        restored=client.post(f"/api/branches/{future['id']}/regress",json={'turn_number':1,'revision':future['revision']}).json()
        assert restored['state'] == base['state']
        assert client.get(f"/api/branches/{future['id']}").json()['state'] == future['state']
        restored=step(client,restored,'날씨가 쌀쌀하군요.',provider)
        inputs=json.dumps([provider.inputs[-1],provider.drafts[-1],provider.reviews[-1]],ensure_ascii=False)
        assert '계몽의 서' not in inputs and '출처_CANARY_832' not in inputs
        assert restored['state']['guard'] == 20
        again=step(client,restored,'계몽의서',provider)
        assert again['state']['guard'] == 30
        assert again['state']['confidential']['source_claims'] == []
        audit=again['debug']['relationship']
        assert audit['before']['guard'] == 20 and audit['after']['guard'] == 30
        assert audit['rules'][-1]['rule'] == 'secret_first_mention'
        # A checkpoint in the middle also retains pending/recheck counters exactly.
        reasked=step(client,again,'그냥 들었죠.',provider,'vague')
        cp=client.post(f"/api/branches/{reasked['id']}/checkpoints",json={'label':'출처 재확인','revision':reasked['revision']}).json()
        done=step(client,reasked,'출처 얘기는 그만하죠.',provider,'evasion')
        restored2=client.post(f"/api/checkpoints/{cp['id']}/restore").json()
        assert restored2['state'] == reasked['state']
        done2=step(client,restored2,'출처는 밝히지 않겠습니다.',provider,'refusal')
        assert done2['state']['guard'] == done['state']['guard'] == 35


def test_no_secret_material_in_actual_payloads_before_mention():
    state=initial_state();turn=Turn(text='중요한 기록이 있나요?',revision=0)
    plan=relationship_plan(state,turn,resolve(state,'speak'))
    context=build_context(state,turn,plan['verdict'],plan)
    context['interaction']={'kind':'conversation','focus':None}
    seen=[]
    def handle(request):
        payload=json.loads(request.content);seen.append(payload)
        title=payload['format']['title']
        raw={'consistent':True,'issues':[]} if title=='DialogueReview' else {'kind':'conversation','action':None,'target':None,'evidence':''}
        return httpx.Response(200,json={'done':True,'message':{'role':'assistant','content':json.dumps(raw)}})
    provider=OllamaProvider(Settings(),transport=httpx.MockTransport(handle))
    provider.interpret(intent_context(state,turn.text))
    seen.append(provider.payload(context))
    provider.review(context,Proposal(dialogue='문서와 장부를 보관하는 곳입니다.',**plan['verdict']))
    packed=json.dumps(seen,ensure_ascii=False)
    for private in ['계몽의 서','계몽의서','overview_only','serin_knows_location']:
        assert private not in packed
    assert 'confidential_context' not in context


@pytest.mark.parametrize('failure_stage',['draft','review'])
def test_source_transition_not_saved_on_later_failure(tmp_path,failure_stage):
    class Failing(ControlledSource):
        def propose(self,context):
            if failure_stage=='draft':raise RuntimeError('실패')
            return super().propose(context)
        def review(self,context,proposal):
            if failure_stage=='review':raise RuntimeError('실패')
            return super().review(context,proposal)
    with TestClient(create_app(tmp_path/'test.sqlite3',provider=Failing())) as client:
        branch=client.post('/api/games').json()
        response=client.post(f"/api/branches/{branch['id']}/chat",json={'text':'계몽의 서','mode':'free','revision':0})
        assert response.status_code==502
        assert client.get(f"/api/branches/{branch['id']}").json()==branch
        assert client.get(f"/api/branches/{branch['id']}/checkpoints").json()==[]


def test_source_answer_schema_only_when_pending_and_budget_fits():
    state=initial_state()
    context=intent_context(state,'안녕')
    assert '$defs' not in intent_schema(context)
    state,_=transact(state,'계몽의 서')
    context=intent_context(state,'출처는 밝히지 않겠습니다.')
    schema=intent_schema(context)
    assert all('source_answer' in choice['required'] for choice in schema['anyOf'])
    assert context['source_check']['last_question'] == state['confidential']['last_question']
    provider=OllamaProvider(Settings())
    provider.structured_stage=lambda messages,schema,validator:provider.stage_payload(messages,schema)
    payload=provider.interpret(context)
    assert payload['options']['num_ctx']==8192
    assert '계몽의 서' not in json.dumps(payload,ensure_ascii=False)


@pytest.mark.parametrize('bad', [
    {'type':'refusal','evidence':'다른 원문'},
    {'type':'unknown','evidence':'답변'},
    {'type':'concrete','evidence':'답변','verified':True},
    None,
])
def test_malformed_ollama_source_response_is_atomic(tmp_path,bad):
    state,_=transact(initial_state(),'계몽의 서')
    path=tmp_path/'test.sqlite3';store=Store(path)
    with store.connect(write=True) as db:
        db.execute('INSERT INTO branches(id,game_id,snapshot) VALUES(?,?,?)',('pending','test',encode(state)))
    def handle(request):
        result={'kind':'conversation','action':None,'target':None,'evidence':''}
        if bad is not None:result['source_answer']=bad
        return httpx.Response(200,json={'done':True,'message':{'role':'assistant','content':json.dumps(result)}})
    provider=OllamaProvider(Settings(),transport=httpx.MockTransport(handle))
    with TestClient(create_app(path,provider=provider)) as client:
        before=client.get('/api/branches/pending').json()
        result=client.post('/api/branches/pending/chat',json={'text':'답변','mode':'free','revision':0})
        assert result.status_code==502
        assert client.get('/api/branches/pending').json()==before
        assert client.get('/api/branches/pending/checkpoints').json()==[]


def test_disabled_adjustment_does_not_disable_semantic_confirmation():
    state=initial_state()
    state['relationship_rules']['rules']['secret_first_mention']['max_applications_per_branch']=0
    state['relationship_rules']['rules']['source_refusal']['max_applications_per_branch']=0
    state,plan=transact(state,'계몽의 서')
    assert state['guard']==20 and state['confidential']['source_status']=='pending'
    assert not plan['audit']['rules'][-1]['applied']
    state,plan=transact(state,'출처는 말할 수 없습니다.','refusal')
    assert state['guard']==20 and state['confidential']['source_status']=='closed'
    assert not state['confidential']['additional_guard_applied']

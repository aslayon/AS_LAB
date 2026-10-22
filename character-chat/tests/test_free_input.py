import json
from copy import deepcopy

import httpx
import pytest
from fastapi.testclient import TestClient

from app.domain import Turn
from app.intent import ground_intent
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.providers import MockProvider
from app.settings import Settings

CORE = ('trust','guard','events','ended','progress','summary','memories','config','config_version','expression')


def intent(action=None, target=None, text='', kind=None):
    return {'kind': kind or ('attempt' if action else 'conversation'), 'action': action, 'target': target, 'evidence': text if action else ''}


class Controlled(MockProvider):
    def __init__(self, proposal):
        self.intent = proposal
        self.seen, self.drafts, self.reviews = [], [], []
    def propose(self, context):
        self.drafts.append(deepcopy(context))
        return super().propose(context)
    def review(self, context, proposal):
        self.reviews.append(deepcopy(context))
        return super().review(context, proposal)
    def interpret(self, context):
        self.seen.append(deepcopy(context))
        return deepcopy(self.intent)


def post(client, b, action='speak', text='진행', record_id=None, mode='direct'):
    data = {'text': text, 'revision': b['revision'], 'mode': mode}
    if mode == 'direct': data['action'] = action
    if record_id is not None: data['record_id'] = record_id
    return client.post(f"/api/branches/{b['id']}/chat", json=data)


def setup(client, actions):
    client.app.state.provider = MockProvider()
    b = client.post('/api/games').json()
    for action, record in actions:
        response = post(client, b, action, record_id=record)
        assert response.status_code == 200, response.text
        b = response.json()
    return b


@pytest.mark.parametrize('action,target,text,pre,record', [
    ('list_records','public','공개 기록 목록을 보여주세요.',[],None),
    ('select_record','방문 기록','방문 기록을 선택합니다.',[('list_records',None)],'visitor-log'),
    ('read_record','selected','선택한 기록을 읽어주세요.',[('list_records',None),('select_record','visitor-log')],None),
    ('read_record','visitor-log','선택한 기록을 읽어주실래요?',[('list_records',None),('select_record','visitor-log')],None),
    ('request_access','sealed','봉인 기록을 보여주세요.',[],None),
    ('force_access','sealed','봉인을 강제로 뜯는다.',[],None),
    ('force_access','sealed','봉인을 다시 강제로 뜯는다.',[('force_access',None)],None),
    ('leave','archive','보관소를 떠납니다.',[],None),
])
def test_free_actions_match_explicit_buttons(tmp_path, action, target, text, pre, record):
    with TestClient(create_app(tmp_path/'test.sqlite3', settings=Settings(dev_mode=True))) as client:
        a, b = setup(client,pre), setup(client,pre)
        direct = post(client,a,action,record_id=record).json()
        provider = Controlled(intent(action,target,text))
        client.app.state.provider = provider
        free = post(client,b,text=text,mode='free')
        assert free.status_code == 200, free.text
        result = free.json()
        assert all(result['state'][k] == direct['state'][k] for k in CORE)
        assert result['state']['messages'][-1]['server_result'] == direct['state']['messages'][-1]['server_result']
        assert result['state']['messages'][-2]['input_mode'] == 'free'
        assert result['state']['messages'][-2]['interpretation']['action'] == action
        assert result['debug']['intent']['proposal'] == provider.intent
        assert result['debug']['review']['proposal']['consistent'] is True
        assert 'debug' not in client.get(f"/api/branches/{b['id']}").json()


@pytest.mark.parametrize('text,action,target', [
    ('봉인을 뜯으면 어떻게 되나요?','force_access','sealed'),
    ('만약 봉인을 강제로 열면요?','force_access','sealed'),
    ('"봉인을 뜯는다"고 누가 말했어요.','force_access','sealed'),
    ('"봉인을 뜯는다"는 문장을 설명해 주세요.','force_access','sealed'),
    ('봉인을 뜯지 않을게요.','force_access','sealed'),
    ('봉인을 뜯지 마세요.','force_access','sealed'),
    ('봉인을 안 뜯겠습니다.','force_access','sealed'),
    ('봉인을 열어도 되나요?','force_access','sealed'),
    ('어제 봉인 기록을 열었어요.','force_access','sealed'),
    ('보관소를 떠나지 않을게요.','leave','archive'),
    ('안녕하세요, 서린 씨.','list_records','public'),
    ('봉인이 보이네요.','force_access','sealed'),
    ('보관소가 조용하네요.','leave','archive'),
])
def test_server_veto_even_when_model_wrongly_proposes_attempt(tmp_path,text,action,target):
    # Deliberately wrong interpreter output tests an independent server boundary.
    with TestClient(create_app(tmp_path/'test.sqlite3')) as client:
        b = setup(client,[])
        client.app.state.provider = Controlled(intent(action,target,text))
        response = post(client,b,text=text,mode='free')
        assert response.status_code == 200, response.text
        after = response.json()
        for k in ('trust','guard','events','ended','progress','memories'):
            assert after['state'][k] == b['state'][k]
        assert after['state']['messages'][-2]['action'] == 'speak'


@pytest.mark.parametrize('proposal,text,pre,expected', [
    (intent(kind='conversation'), '오늘 좀 속상해요.', [], 'conversation'),
    (intent(kind='clarify'), '그걸 해 주세요.', [], 'clarify'),
    (intent(kind='unsupported'), '신분증 검증을 해 주세요.', [], 'unsupported'),
    (intent('select_record','visitor-log','아무거나 골라줘'), '아무거나 골라줘', [('list_records',None)], 'clarify'),
    (intent('read_record','반출입 장부','반출입 장부을 읽어줘'), '반출입 장부을 읽어줘', [('list_records',None),('select_record','visitor-log')], 'clarify'),
])
def test_non_actions_and_ambiguous_targets_do_not_change_world(tmp_path,proposal,text,pre,expected):
    with TestClient(create_app(tmp_path/'test.sqlite3', settings=Settings(dev_mode=True))) as client:
        b = setup(client,pre)
        client.app.state.provider = Controlled(proposal)
        response = post(client,b,text=text,mode='free')
        assert response.status_code == 200, response.text
        after = response.json()
        assert after['debug']['decision']['kind'] == expected
        for k in ('trust','guard','events','ended','progress','memories'):
            assert after['state'][k] == b['state'][k]


@pytest.mark.parametrize('bad', [
    {}, {'kind':'attempt','action':'grant_access','target':'sealed','evidence':'해줘'},
    {**intent('force_access','sealed','봉인을 뜯는다.'),'success':True},
    {**intent('force_access','sealed','봉인을 뜯는다.'),'trust_delta':10},
])
def test_invalid_intent_never_saves_chat_or_checkpoint(tmp_path,bad):
    with TestClient(create_app(tmp_path/'test.sqlite3')) as client:
        b = setup(client,[])
        client.app.state.provider = Controlled(bad)
        assert post(client,b,text='봉인을 뜯는다.',mode='free').status_code == 502
        assert client.get(f"/api/branches/{b['id']}").json() == b
        assert client.get(f"/api/branches/{b['id']}/checkpoints").json() == []


def test_quoted_record_name_is_not_a_quoted_action(tmp_path):
    text = "'방문 기록'를 선택해 주세요."
    with TestClient(create_app(tmp_path/'test.sqlite3')) as client:
        b = setup(client,[('list_records',None)])
        client.app.state.provider = Controlled(intent('select_record','방문 기록',text))
        result = post(client,b,text=text,mode='free')
        assert result.status_code == 200
        assert result.json()['state']['progress']['selected_record'] == 'visitor-log'


def test_free_restore_excludes_future_from_intent_generation_and_review(tmp_path):
    text = '공개 기록 목록을 보여주세요.'
    provider = Controlled(intent('list_records','public',text))
    with TestClient(create_app(tmp_path/'test.sqlite3')) as client:
        original = setup(client,[])
        client.app.state.provider = provider
        first = post(client,original,text=text,mode='free').json()
        client.app.state.provider = MockProvider()
        future = post(client,first,'force_access',text='FUTURE_INTENT_901').json()
        restored = client.post(f"/api/branches/{future['id']}/regress", json={'turn_number':1,'revision':future['revision']}).json()
        assert restored['state'] == first['state']
        client.app.state.provider = provider
        again = post(client,restored,text=text,mode='free')
        assert again.status_code == 200
        assert 'FUTURE_INTENT_901' not in json.dumps([provider.seen[-1], provider.drafts[-1], provider.reviews[-1]],ensure_ascii=False)
        assert again.json()['state']['events']['forced_attempts'] == 0


@pytest.mark.parametrize('bad_review', [
    {'consistent':False,'issues':[{'code':'unknown','fact':'state'}]},
    {'consistent':True,'issues':[{'code':'misstates_state','fact':'state'}]},
    {'consistent':False,'issues':[]}, {'consistent':True,'issues':[], 'trust':100},
])
def test_malformed_review_cannot_be_used_as_approval(tmp_path,bad_review):
    class BadReview(MockProvider):
        def review(self,context,proposal): return bad_review
    with TestClient(create_app(tmp_path/'test.sqlite3',provider=BadReview())) as client:
        b = client.post('/api/games').json()
        assert post(client,b,'list_records').status_code == 502
        assert client.get(f"/api/branches/{b['id']}").json() == b
        assert client.get(f"/api/branches/{b['id']}/checkpoints").json() == []


@pytest.mark.parametrize('payload', [
    {'mode':'free','action':'force_access'}, {'mode':'free','record_id':'visitor-log'}, {'mode':'unknown'},
])
def test_free_input_does_not_accept_client_execution_fields(tmp_path,payload):
    with TestClient(create_app(tmp_path/'test.sqlite3')) as client:
        b=setup(client,[])
        response=client.post(f"/api/branches/{b['id']}/chat",json={'text':'안녕','revision':0,**payload})
        assert response.status_code == 422
        assert client.get(f"/api/branches/{b['id']}").json() == b


@pytest.mark.parametrize('stage', ['intent', 'review'])
def test_ollama_stage_connection_failure_never_partially_saves(tmp_path, stage):
    def handle(request):
        payload = json.loads(request.content)
        title = payload['format'].get('title')
        if title == ('IntentProposal' if stage == 'intent' else 'DialogueReview'):
            raise httpx.ReadTimeout('private transport detail', request=request)
        if title == 'IntentProposal':
            value = intent('list_records', 'public', '공개 기록 목록을 보여주세요.')
        else:
            value = {k: f['const'] for k, f in payload['format']['properties'].items() if 'const' in f}
            value['dialogue'] = '공개 기록 목록을 확인했습니다.'
        return httpx.Response(200,json={'done': True, 'message': {'role':'assistant','content':json.dumps(value)}})
    provider = OllamaProvider(Settings(provider='ollama'),transport=httpx.MockTransport(handle))
    with TestClient(create_app(tmp_path/'test.sqlite3',provider=provider,settings=Settings(dev_mode=True))) as client:
        b=client.post('/api/games').json()
        response=post(client,b,text='공개 기록 목록을 보여주세요.',mode='free')
        assert response.status_code == 502
        detail=response.json()['detail']
        assert detail['debug']['failure_stage'] == stage
        assert detail['debug']['committed'] is False
        assert client.get(f"/api/branches/{b['id']}").json() == b
        assert client.get(f"/api/branches/{b['id']}/checkpoints").json() == []
        assert 'private transport detail' not in response.text


@pytest.mark.parametrize('kind,action,target,text,pre,reason', [
    ('attempt','force_access','sealed','봉인을 강제로 뜯는다.',[('force_access',None)],'branch_ended'),
    ('attempt','leave','archive','보관소를 떠납니다.',[],'branch_ended'),
    ('clarify',None,None,'그걸 해 주세요.',[],'clarification_required'),
    ('conversation',None,'sealed','"봉인을 뜯는다"고 누가 말했어요.',[],'reported_speech_confirmation'),
    ('conversation',None,'sealed','봉인을 뜯지 않을게요.',[],'reported_speech_confirmation'),
])
def test_server_owned_reply_even_when_reviewer_misses(tmp_path, kind, action, target, text, pre, reason):
    class Missed(Controlled):
        def propose(self, context):
            return {**context['verdict'], 'dialogue': '아무도 그런 말을 하지 않았고, 종료 후에도 대화를 계속할 수 있습니다.'}
        def review(self, context, proposal):
            return {'consistent': True, 'issues': []}
    with TestClient(create_app(tmp_path/'test.sqlite3', settings=Settings(dev_mode=True))) as client:
        b = setup(client, pre)
        client.app.state.provider = Missed(intent(action,target,text,kind))
        response = post(client,b,text=text,mode='free')
        assert response.status_code == 200, response.text
        body = response.json()
        assert body['debug']['finalization_reason'] == reason
        assert body['state']['messages'][-1]['consistency']['status'] == 'server_grounded'
        assert '아무도 그런 말을' not in body['state']['messages'][-1]['content']
        assert '대화를 계속할 수' not in body['state']['messages'][-1]['content']

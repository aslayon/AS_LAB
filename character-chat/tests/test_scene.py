"""Audience separation and old-snapshot compatibility, independent of wording quality."""
import json
from copy import deepcopy
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.domain import Turn, initial_state, resolve, advance_state
from app.intent import intent_context
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.providers import build_context
from app.settings import Settings
from app.store import Store, encode


def test_author_player_and_unknown_config_fields_never_reach_model_calls():
    state = initial_state()
    state['config']['author_notes'] = {'secret': 'AUTHOR_PRIVATE_CANARY_817'}
    state['config']['player_only'] = {'purpose': 'PLAYER_PRIVATE_CANARY_294'}
    state['config']['future_unknown'] = 'UNKNOWN_PRIVATE_CANARY_528'
    requests = []
    turn = Turn(text='이곳 이야기를 듣고 싶어요.', revision=0)
    verdict = resolve(state, 'speak')
    context = build_context(state, turn, verdict)
    context['interaction'] = {'kind': 'conversation', 'focus': None}
    def respond(request):
        payload = json.loads(request.content)
        requests.append(payload)
        title = payload['format']['title']
        if title == 'IntentProposal':
            result = {'kind':'conversation','action':None,'target':None,'evidence':''}
        elif title == 'DialogueReview':
            result = {'consistent':True,'issues':[]}
        else:
            result = {'dialogue':'문서와 장부를 보관하고 있습니다.',**verdict}
        return httpx.Response(200,json={'done':True,'message':{'role':'assistant','content':json.dumps(result)}})
    provider = OllamaProvider(Settings(provider='ollama'),transport=httpx.MockTransport(respond))
    provider.interpret(intent_context(state, turn.text))
    from app.domain import Proposal
    draft = provider.propose(deepcopy(context))
    provider.review(context,Proposal.model_validate(draft.proposal))
    assert len(requests) == 3
    packed = json.dumps([intent_context(state,turn.text),context,requests],ensure_ascii=False)
    for canary in ('AUTHOR_PRIVATE_CANARY_817','PLAYER_PRIVATE_CANARY_294','UNKNOWN_PRIVATE_CANARY_528'):
        assert canary not in packed
    assert state['config']['environment'] in requests[1]['messages'][0]['content']
    assert state['config']['known_facts'][0] in requests[1]['messages'][0]['content']


def test_smalltalk_receives_observed_events_and_relationship_not_player_motive():
    state = initial_state()
    attempt = Turn(text='봉인 강제 접근 시도',action='force_access',revision=0)
    state = advance_state(state,attempt,resolve(state,attempt.action))
    text = '이야기를 계속할 수 있나요?'
    turn = Turn(text=text,revision=0)
    context = build_context(state,turn,resolve(state,'speak'))
    context['interaction'] = {'kind':'conversation','focus':None}
    system = OllamaProvider(Settings()).payload(context)['messages'][0]['content']
    assert 'warning' in system
    assert '"trust":15' in system and '"guard":45' in system
    assert '몰래' not in system and '훔쳐' not in system


def test_old_config_records_checkpoints_and_branches_survive_new_game(tmp_path):
    legacy = json.loads((Path(__file__).parent/'fixtures/archive-2.0-snapshot.json').read_text())
    path = tmp_path/'test.sqlite3'
    store = Store(path)
    with store.connect(write=True) as db:
        db.execute('INSERT INTO branches(id,game_id,snapshot) VALUES(?,?,?)',('legacy','old-game',encode(legacy)))
    with TestClient(create_app(path)) as client:
        old = client.get('/api/branches/legacy').json()
        assert old['state'] == legacy
        cp = client.post('/api/branches/legacy/checkpoints',json={'label':'old config','revision':0}).json()
        for action,record_id in [('list_records',None),('select_record','rain-log'),('read_record',None)]:
            payload = {'text':'기존 경로','action':action,'revision':old['revision']}
            if action == 'select_record':
                # Keep the pre-existing mock free-input example on legacy records.
                payload = {'text': legacy['config']['public_records'][0]['title']+'를 선택합니다.',
                           'mode':'free','revision':old['revision']}
            response = client.post('/api/branches/legacy/chat',json=payload)
            assert response.status_code == 200,response.text
            old = response.json()
        assert old['state']['config'] == legacy['config']
        assert old['state']['messages'][-1]['server_result']['record'] == legacy['config']['public_records'][0]
        restored = client.post(f"/api/checkpoints/{cp['id']}/restore").json()
        assert restored['id'] != old['id'] and restored['state'] == legacy
        new = client.post('/api/games').json()
        assert new['state']['config_version'] == 'archive-5.0'
        assert new['state']['config'] != legacy['config']
        assert client.get('/api/branches/legacy').json()['state'] == old['state']
        assert 'known_facts' not in build_context(legacy,Turn(text='안내 부탁드립니다.',revision=0),resolve(legacy,'speak'))['instructions']

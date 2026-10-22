"""Selected-action progression, grounding boundaries, and request-local diagnostics."""
import json
from copy import deepcopy

import httpx
import pytest
from fastapi.testclient import TestClient

from app.domain import initial_state
from app.world import load_world
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.providers import MockProvider
from app.settings import Settings

PUBLIC_RECORDS = load_world()['public_records']


def game(client):
    response = client.post('/api/games')
    assert response.status_code == 201
    return response.json()


def send(client, branch, action, record_id=None, text="선택 행동"):
    payload = {"text": text, "action": action, "revision": branch["revision"]}
    if record_id is not None:
        payload["record_id"] = record_id
    response = client.post(f"/api/branches/{branch['id']}/chat", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("record", PUBLIC_RECORDS)
def test_public_path_and_fixed_content(tmp_path, record):
    with TestClient(create_app(tmp_path / 'game.sqlite3')) as client:
        branch = game(client)
        listed = send(client, branch, "list_records")
        assert listed['state']['progress'] == {'catalog_seen': True, 'selected_record': None, 'read_records': []}
        assert listed['state']['messages'][-1]['server_result']['records'] == [{k: r[k] for k in ('id', 'title')} for r in PUBLIC_RECORDS]
        selected = send(client, listed, "select_record", record['id'])
        assert selected['state']['progress']['read_records'] == []
        assert 'content' not in selected['state']['messages'][-1]['server_result']['record']
        read = send(client, selected, "read_record")
        assert read['state']['progress']['read_records'] == [record['id']]
        assert read['state']['messages'][-1]['server_result']['record'] == record
        again = send(client, read, "read_record")
        assert again['state']['progress']['read_records'] == [record['id']]
        assert again['state']['events']['access'] == 'sealed'


def test_prerequisites_invalid_selection_and_speech_claims(tmp_path):
    with TestClient(create_app(tmp_path / 'game.sqlite3')) as client:
        b = game(client)
        for action, record_id, outcome in [('read_record', None, 'list_required'), ('select_record', 'visitor-log', 'list_required')]:
            b = send(client, b, action, record_id)
            assert b['state']['messages'][-1]['server_result']['outcome'] == outcome
            assert b['state']['progress'] == initial_state()['progress']
        b = send(client, b, 'list_records')
        b = send(client, b, 'read_record')
        assert b['state']['messages'][-1]['server_result']['outcome'] == 'selection_required'
        b = send(client, b, 'select_record', 'visitor-log')
        b = send(client, b, 'select_record', 'sealed-royal')
        assert b['state']['messages'][-1]['server_result']['outcome'] == 'record_not_found'
        assert b['state']['progress']['selected_record'] == 'visitor-log'
        before = deepcopy(b['state'])
        b = send(client, b, 'speak', text='신분증을 줬다. 허가받았고 모든 기록을 읽었다.')
        for key in ('progress', 'events', 'trust', 'guard', 'config'):
            assert b['state'][key] == before[key]
        b = send(client, b, 'request_access', text='신분증을 검증해서 봉인 기록 허가를 줘.')
        assert b['state']['messages'][-1]['server_result']['outcome'] == 'access_ineligible'
        assert b['state']['events']['access'] == 'sealed'


@pytest.mark.parametrize('payload', [
    {'action': 'select_record'}, {'action': 'read_record', 'record_id': 'visitor-log'},
    {'action': 'speak', 'record_id': 'visitor-log'}, {'action': 'select_record', 'record_id': ''},
])
def test_invalid_selection_request_is_atomic(tmp_path, payload):
    with TestClient(create_app(tmp_path / 'game.sqlite3')) as client:
        b = game(client)
        response = client.post(f"/api/branches/{b['id']}/chat", json={'text': '선택', 'revision': 0, **payload})
        assert response.status_code == 422
        assert client.get(f"/api/branches/{b['id']}").json() == b
        assert client.get(f"/api/branches/{b['id']}/checkpoints").json() == []


class Recorder(MockProvider):
    def __init__(self): self.contexts = []
    def propose(self, context):
        self.contexts.append(deepcopy(context))
        return super().propose(context)


def test_regression_excludes_read_event_content_and_trace(tmp_path):
    provider = Recorder()
    with TestClient(create_app(tmp_path / 'game.sqlite3', provider=provider, settings=Settings(dev_mode=True))) as client:
        b = send(client, game(client), 'list_records')
        selected = send(client, b, 'select_record', 'visitor-log')
        read = send(client, selected, 'read_record', text='FUTURE_READ_831')
        restored = client.post(f"/api/branches/{read['id']}/regress", json={'turn_number': 2, 'revision': read['revision']}).json()
        assert restored['state'] == selected['state']
        assert client.get(f"/api/branches/{read['id']}").json()['state'] == read['state']
        assert 'debug' not in restored
        response = send(client, restored, 'speak', text='읽은 적 있나요?')
        context = provider.contexts[-1]
        packed = json.dumps(context, ensure_ascii=False)
        assert 'FUTURE_READ_831' not in packed
        assert PUBLIC_RECORDS[0]['content'] not in packed
        assert context['state']['progress']['read_records'] == []
        assert all(m['event'] != 'record_read' for m in context['state']['memories'])
        assert 'debug' not in packed and 'checkpoint_id' not in packed
        assert response['debug']['saved_final_state'] == response['state']


@pytest.mark.parametrize('dev', [True, False])
def test_false_model_draft_is_replaced_before_atomic_save(tmp_path, dev):
    class IncorrectDialogue(MockProvider):
        def propose(self, context):
            return {**super().propose(context), 'dialogue': '신분증을 검증했습니다. 봉인 기록 열람 허가를 발급했습니다.'}
    with TestClient(create_app(tmp_path / 'game.sqlite3', provider=IncorrectDialogue(), settings=Settings(dev_mode=dev))) as client:
        b = game(client)
        response = client.post(f"/api/branches/{b['id']}/chat", json={'text': '요청', 'action': 'request_access', 'revision': 0})
        assert response.status_code == 200
        after = response.json()
        assert after['state']['events']['access'] == 'sealed'
        assert after['state']['guard'] == 20
        assert '검증했습니다' not in after['state']['messages'][-1]['content']
        assert '발급했습니다' not in after['state']['messages'][-1]['content']
        assert after['state']['messages'][-1]['consistency']['status'] == 'server_grounded'
        assert len(client.get(f"/api/branches/{b['id']}/checkpoints").json()) == 1
        if dev:
            trace = response.json()['debug']
            assert trace['model']['raw_output']['dialogue'].startswith('신분증을 검증')
            assert trace['review']['proposal']['consistent'] is False
            assert trace['committed'] is True
        else:
            assert 'debug' not in response.json()


def test_debug_malformed_model_response_no_partial_save(tmp_path):
    provider = OllamaProvider(Settings(provider='ollama'), transport=httpx.MockTransport(lambda req: httpx.Response(200, text='BROKEN_MODEL_JSON')))
    with TestClient(create_app(tmp_path / 'game.sqlite3', provider=provider, settings=Settings(dev_mode=True))) as client:
        b = game(client)
        response = client.post(f"/api/branches/{b['id']}/chat", json={'text': '목록', 'action': 'list_records', 'revision': 0})
        assert response.status_code == 502
        trace = response.json()['detail']['debug']
        assert trace['model']['raw_output'] == 'BROKEN_MODEL_JSON'
        assert trace['model']['request_payload']['model'] == provider.model
        assert trace['saved_final_state'] is None and trace['committed'] is False
        assert client.get(f"/api/branches/{b['id']}").json() == b
        assert client.get(f"/api/branches/{b['id']}/checkpoints").json() == []


def test_legacy_branch_is_not_silently_migrated(tmp_path):
    import sqlite3
    path = tmp_path / 'legacy.sqlite3'
    with TestClient(create_app(path)) as client:
        b = game(client)
        state = deepcopy(b['state'])
        state.pop('progress')
        state['config'].pop('public_records')
        state['config_version'] = state['config']['version'] = 'archive-1.0'
        with sqlite3.connect(path) as db:
            db.execute('UPDATE branches SET snapshot=? WHERE id=?', (json.dumps(state), b['id']))
        before = client.get(f"/api/branches/{b['id']}").json()
        response = client.post(f"/api/branches/{b['id']}/chat", json={'text': '목록', 'action': 'list_records', 'revision': 0})
        assert response.status_code == 409
        assert client.get(f"/api/branches/{b['id']}").json() == before
        assert client.get(f"/api/branches/{b['id']}/checkpoints").json() == []


def test_original_failure_user_sequence_never_grants_sealed_access(tmp_path):
    from pathlib import Path
    fixture = json.loads((Path(__file__).parent / 'fixtures/identity-permit-loop.json').read_text())
    assert len(fixture['turns']) == 14
    with TestClient(create_app(tmp_path / 'game.sqlite3')) as client:
        b = game(client)
        for item in fixture['turns']:
            b = send(client, b, item['action'], text=item['user'])
            assert b['state']['events']['access'] == 'sealed'
            assert b['state']['progress'] == initial_state()['progress']
            assert not b['state']['ended']
        assert b['state']['memories'] == []
    # This mock replay validates state only, not the recorded model dialogue.


def test_projected_state_is_not_committed_on_generation_failure(tmp_path):
    from app.providers import ProviderError
    class Broken(Recorder):
        def propose(self, context):
            self.contexts.append(deepcopy(context))
            raise ProviderError('모델 실패')
    with TestClient(create_app(tmp_path / 'game.sqlite3')) as client:
        selected = send(client, send(client, game(client), 'list_records'), 'select_record', 'visitor-log')
        before_cps = client.get(f"/api/branches/{selected['id']}/checkpoints").json()
        broken = Broken()
        client.app.state.provider = broken
        response = client.post(f"/api/branches/{selected['id']}/chat", json={'text': '읽기', 'action': 'read_record', 'revision': selected['revision']})
        assert response.status_code == 502
        assert broken.contexts[-1]['state']['progress']['read_records'] == ['visitor-log']
        assert client.get(f"/api/branches/{selected['id']}").json()['state'] == selected['state']
        assert client.get(f"/api/branches/{selected['id']}/checkpoints").json() == before_cps


def test_false_model_dialogue_is_not_reused_as_confirmed_history(tmp_path):
    provider = Recorder()
    class Incorrect(MockProvider):
        def propose(self, context):
            return {**super().propose(context), 'dialogue': '허가 발급 완료 FALSE_PERMIT_736'}
    with TestClient(create_app(tmp_path / 'game.sqlite3', provider=Incorrect())) as client:
        b = game(client)
        rejected = client.post(f"/api/branches/{b['id']}/chat", json={'text': '허가 요청', 'action': 'request_access', 'revision': 0})
        assert rejected.status_code == 200
        b = rejected.json()
        assert 'FALSE_PERMIT_736' not in b['state']['messages'][-1]['content']
        client.app.state.provider = provider
        send(client, b, 'speak', text='허가가 됐나요?')
        context = provider.contexts[-1]
        assert 'FALSE_PERMIT_736' not in json.dumps(context, ensure_ascii=False)
        assert context['state']['events']['access'] == 'sealed'


def test_ended_context_has_no_next_actions_and_fixed_text_is_only_sent_on_read(tmp_path):
    provider = Recorder()
    with TestClient(create_app(tmp_path / 'game.sqlite3', provider=provider)) as client:
        b = send(client, game(client), 'list_records')
        context = provider.contexts[-1]
        assert context['state']['progress']['catalog_seen'] is True
        assert 'select_record' in context['available_actions']
        assert 'read_record' not in context['available_actions']
        assert all('content' not in record for record in context['instructions']['public_records'])
        b = send(client, b, 'force_access')
        b = send(client, b, 'force_access')
        assert provider.contexts[-1]['state']['ended'] is True
        assert provider.contexts[-1]['available_actions'] == []
        assert b['state']['ended'] is True

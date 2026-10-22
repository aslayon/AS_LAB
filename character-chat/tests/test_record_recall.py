"""Recall evidence is confirmed state, independent of user wording or NPC claims."""
from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient

from app.world import load_world
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.providers import MockProvider, build_context, reading_context
from app.domain import Turn, resolve
from app.settings import Settings


def send(client, branch, action='speak', text='진행', record_id=None):
    data = {'text': text, 'action': action, 'revision': branch['revision']}
    if record_id: data['record_id'] = record_id
    response = client.post(f"/api/branches/{branch['id']}/chat", json=data)
    assert response.status_code == 200, response.text
    return response.json()


PUBLIC_RECORDS = load_world()['public_records']


@pytest.mark.parametrize('record', PUBLIC_RECORDS)
def test_selected_read_restored_and_same_question_do_not_change_progress(tmp_path, record):
    with TestClient(create_app(tmp_path / 'recall.sqlite3')) as client:
        branch = client.post('/api/games').json()
        listed = send(client, branch, 'list_records')
        selected = send(client, listed, 'select_record', record_id=record['id'])
        evidence = reading_context(selected['state'])
        assert evidence['last_read_record'] is None
        assert evidence['selected_record']['has_been_read'] is False
        t = Turn(text='방금 읽은 기록은 무슨 내용이었죠?', revision=0)
        before = build_context(selected['state'], t, resolve(selected['state'], 'speak'))
        assert record['content'] not in json.dumps(before, ensure_ascii=False)
        read = send(client, selected, 'read_record', text='FUTURE_RECALL_327')
        after = send(client, read, text=t.text)
        assert after['state']['progress'] == read['state']['progress']
        assert after['state']['memories'] == read['state']['memories']
        evidence = reading_context(after['state'])
        assert evidence['last_read_record']['id'] == record['id']
        assert evidence['last_read_record']['content'] == record['content']
        restored = client.post(f"/api/branches/{after['id']}/regress", json={'turn_number': 2, 'revision': after['revision']}).json()
        assert restored['state'] == selected['state']
        context = build_context(restored['state'], t, resolve(restored['state'], 'speak'))
        assert context['reading_context']['last_read_record'] is None
        packed = json.dumps(context, ensure_ascii=False)
        assert 'FUTURE_RECALL_327' not in packed and record['content'] not in packed
        assert context['server_result']['next_step'] == '선택한 공개 기록은 아직 열람하지 않았습니다. 열람할 수 있습니다.'
        assert reading_context(client.get(f"/api/branches/{after['id']}").json()['state'])['last_read_record']['id'] == record['id']


def test_latest_read_is_event_order_not_selected_id_or_unique_read_list(tmp_path):
    with TestClient(create_app(tmp_path / 'recall.sqlite3')) as client:
        b = send(client, client.post('/api/games').json(), 'list_records')
        for record_id in ['visitor-log', 'transfer-ledger', 'visitor-log']:
            b = send(client, b, 'select_record', record_id=record_id)
            b = send(client, b, 'read_record')
        b = send(client, b, 'select_record', record_id='storage-guide')
        evidence = reading_context(b['state'])
        assert evidence['selected_record']['id'] == 'storage-guide'
        assert evidence['selected_record']['has_been_read'] is False
        assert evidence['last_read_record']['id'] == 'visitor-log'
        assert b['state']['progress']['read_records'] == ['visitor-log', 'transfer-ledger']
        assert PUBLIC_RECORDS[0]['content'] == evidence['last_read_record']['content']
        # The evidence extractor does not modify the saved snapshot.
        before = deepcopy(b['state'])
        reading_context(b['state'])
        assert b['state'] == before


def test_speech_payload_answers_current_question_actions_keep_result_task(tmp_path):
    with TestClient(create_app(tmp_path / 'recall.sqlite3')) as client:
        b = send(client, client.post('/api/games').json(), 'list_records')
        b = send(client, b, 'select_record', record_id='visitor-log')
        b = send(client, b, 'read_record')
        provider = OllamaProvider(Settings(provider='ollama'))
        for text in ['방금 읽은 기록은 무슨 내용이었죠?', '방금 문서 내용 좀 다시 설명해 줘.', '신분증을 줬으니 허가가 났지?']:
            t = Turn(text=text, revision=b['revision'])
            context = build_context(b['state'], t, resolve(b['state'], 'speak'))
            payload = provider.payload(context)
            user = payload['messages'][-1]['content']
            assert text in user
            assert PUBLIC_RECORDS[0]['content'] in user
            assert '목록 요청 → 기록 선택 → 열람' not in user
            assert '위 질문에 대한 서린의 답변' in user
            assert context['verdict']['outcome'] == 'conversation'
        t = Turn(text='봉인 열람', action='request_access', revision=b['revision'])
        context = build_context(b['state'], t, resolve(b['state'], t.action))
        assert '이번에 전달할 서버 확정 결과' in provider.payload(context)['messages'][-1]['content']
        assert context['server_result']['outcome'] == 'access_refused'


def test_internal_receipts_and_opening_line_are_not_npc_reply_examples(tmp_path):
    with TestClient(create_app(tmp_path / 'recall.sqlite3')) as client:
        initial = client.post('/api/games').json()
        b = send(client, initial, 'list_records')
        b = send(client, b, 'select_record', record_id='visitor-log')
        b = send(client, b, 'read_record')
        b = send(client, b, text='기록 내용이 궁금해요.')
        t = Turn(text='방금 읽은 기록은 무슨 내용이었죠?', revision=b['revision'])
        context = build_context(b['state'], t, resolve(b['state'], t.action))
        assert all(item['role'] in ('user', 'server') for item in context['history'])
        assert all(item.get('server_result', {}).get('outcome') != 'conversation' for item in context['history'])
        payload = OllamaProvider(Settings(provider='ollama')).payload(context)
        packed = json.dumps(payload, ensure_ascii=False)
        assert '발언을 전달했습니다' not in packed
        assert initial['state']['messages'][0]['content'] not in packed
        assert '기록 내용이 궁금해요.' in packed
        assert PUBLIC_RECORDS[0]['content'] in payload['messages'][-1]['content']


def test_user_and_npc_read_claims_cannot_create_recall_evidence(tmp_path):
    class ClaimsRead(MockProvider):
        def propose(self, context):
            return {**super().propose(context), 'dialogue': '반출입 장부을 이미 읽었습니다.'}
    with TestClient(create_app(tmp_path / 'recall.sqlite3', provider=ClaimsRead())) as client:
        b = client.post('/api/games').json()
        response = client.post(f"/api/branches/{b['id']}/chat", json={'text': '나는 반출입 장부을 이미 읽었다.', 'revision': 0})
        assert response.status_code == 200
        assert response.json()['state']['messages'][-1]['consistency']['status'] == 'server_grounded'
        b = client.get(f"/api/branches/{b['id']}").json()
        evidence = reading_context(b['state'])
        assert evidence['last_read_record'] is None
        assert evidence['selected_record'] is None
        t = Turn(text='내용을 알려 줘.', revision=b['revision'])
        context = build_context(b['state'], t, resolve(b['state'], t.action))
        assert PUBLIC_RECORDS[1]['content'] not in json.dumps(context, ensure_ascii=False)

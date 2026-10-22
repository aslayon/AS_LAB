"""Selection target contract, including the captured EXAONE failure."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.domain import Turn, initial_state
from app.intent import ground_intent, intent_context, intent_schema, validate_intent
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.settings import Settings


def test_schema_targets_are_action_specific_and_branch_local():
    state = initial_state()
    state['config']['public_records'] = [{'id': 'old-record', 'title': '옛 기록', 'content': '본문'}]
    context = intent_context(state, '옛 기록 선택합니다.')
    schema = intent_schema(context)
    choices = {b['properties']['action']['enum'][0]: b for b in schema['anyOf']}
    assert choices['select_record']['properties']['target']['enum'] == ['old-record']
    assert choices['list_records']['properties']['target']['enum'] == ['public']
    assert context['selection_targets'] == {'옛 기록': 'old-record'}
    assert 'visitor-log' not in json.dumps(schema)
    value = {'kind': 'attempt', 'action': 'select_record', 'target': 'old-record', 'evidence': context['text']}
    assert validate_intent(context, value).target == 'old-record'
    for target in ['public', 'visitor-log', '옛 기록', None]:
        with pytest.raises(ValueError):
            validate_intent(context, {**value, 'target': target})


def test_captured_public_selection_is_never_remapped():
    state = initial_state()
    request = Turn(text='방문 기록을 선택할게요.', revision=0, mode='free')
    raw = {'kind': 'attempt', 'action': 'select_record', 'target': 'public', 'evidence': request.text}
    decision = ground_intent(state, request, raw)
    assert decision.kind == 'clarify'
    assert decision.turn.record_id is None
    assert state['progress']['selected_record'] is None


@pytest.mark.parametrize('target', ['public', 'missing-id'])
def test_invalid_selection_is_atomic(tmp_path, target):
    def handle(request):
        raw = {'kind': 'attempt', 'action': 'select_record', 'target': target, 'evidence': '방문 기록을 선택할게요.'}
        return httpx.Response(200, json={'done': True, 'message': {'role': 'assistant', 'content': json.dumps(raw)}})
    settings = Settings(provider='ollama')
    provider = OllamaProvider(settings, transport=httpx.MockTransport(handle))
    with TestClient(create_app(tmp_path / 'test.sqlite3', provider=provider, settings=settings)) as client:
        branch = client.post('/api/games').json()
        response = client.post(f"/api/branches/{branch['id']}/chat", json={'text': '방문 기록을 선택할게요.', 'mode': 'free', 'revision': 0})
        assert response.status_code == 502
        assert client.get(f"/api/branches/{branch['id']}").json() == branch
        assert client.get(f"/api/branches/{branch['id']}/checkpoints").json() == []


def test_interpret_prompt_uses_branch_titles_and_canonical_ids():
    state = initial_state()
    state['config']['public_records'] = [{'id': 'legacy-id', 'title': '옛 문서', 'content': '노출 금지 본문'}]
    context = intent_context(state, '옛 문서 선택합니다.')
    seen = []
    def handle(request):
        payload = json.loads(request.content)
        seen.append(payload)
        return httpx.Response(200, json={'done': True, 'message': {'role': 'assistant', 'content': json.dumps(
            {'kind':'attempt','action':'select_record','target':'legacy-id','evidence':context['text']})}})
    result = OllamaProvider(Settings(provider='ollama'), transport=httpx.MockTransport(handle)).interpret(context)
    assert result.proposal['target'] == 'legacy-id'
    packed = json.dumps(seen, ensure_ascii=False)
    assert '옛 문서' in packed and 'legacy-id' in packed
    assert 'visitor-log' not in packed and '노출 금지 본문' not in packed


def test_default_ollama_model_and_qwen_override(monkeypatch):
    monkeypatch.delenv('OLLAMA_MODEL', raising=False)
    monkeypatch.delenv('CHARACTER_CHAT_PROVIDER', raising=False)
    assert Settings.from_env().provider == 'mock'
    assert Settings.from_env().ollama_model == 'exaone3.5:7.8b-instruct-q4_K_M'
    monkeypatch.setenv('OLLAMA_MODEL', 'qwen3:4b-instruct-2507-q4_K_M')
    assert Settings.from_env().ollama_model == 'qwen3:4b-instruct-2507-q4_K_M'

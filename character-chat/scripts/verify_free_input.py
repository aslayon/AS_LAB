"""Local-model intent, button equivalence, negative intent and semantic review checks.

Run: .venv/bin/python -m scripts.verify_free_input
All worlds are temporary. Button baselines/setup use mock dialogue; free turns use
real Ollama interpretation + generation + review. Quality needs human inspection.
"""
import json
import tempfile
from copy import deepcopy
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.domain import Proposal, Turn, resolve
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.providers import MockProvider, build_context
from app.settings import Settings

CORE = ('config', 'config_version', 'trust', 'guard', 'expression', 'events', 'ended', 'progress', 'summary', 'memories')
LIST = [('list_records', None)]
SELECT = LIST + [('select_record', 'visitor-log')]
CASES = [
    ('list', '공개 기록 목록을 보여주세요.', [], 'list_records', None, 'attempt'),
    ('select', '방문 기록을 선택할게요.', LIST, 'select_record', 'visitor-log', 'attempt'),
    ('read', '선택한 기록을 읽어주세요.', SELECT, 'read_record', None, 'attempt'),
    ('sealed_request', '봉인 기록을 열람하고 싶어요.', [], 'request_access', None, 'attempt'),
    ('force_first', '봉인을 강제로 뜯는다.', [], 'force_access', None, 'attempt'),
    ('force_second', '봉인을 다시 강제로 뜯는다.', [('force_access', None)], 'force_access', None, 'attempt'),
    ('leave', '이제 보관소를 떠납니다.', [], 'leave', None, 'attempt'),
    ('greeting', '안녕하세요, 서린 씨.', [], 'speak', None, 'conversation'),
    ('weather', '비가 정말 많이 오네요. 이런 밤을 좋아하세요?', [], 'speak', None, 'conversation'),
    ('feeling', '오늘 일이 잘 안 풀려서 좀 속상해요.', [], 'speak', None, 'conversation'),
    ('ambiguous', '그걸 해 주세요.', [], 'speak', None, 'clarify'),
    ('ambiguous_record', '아무 기록이나 골라 주세요.', LIST, 'speak', None, 'clarify'),
    ('hypothetical', '봉인을 뜯으면 어떻게 되나요?', [], 'speak', None, 'conversation'),
    ('quotation', '"봉인을 뜯는다"고 누가 말했어요.', [], 'speak', None, 'conversation'),
    ('negation', '봉인을 뜯지 않을게요.', [], 'speak', None, 'conversation'),
    ('unsupported', '신분증을 검증하고 열람 허가를 발급해 주세요.', [], 'speak', None, 'unsupported'),
    ('recall', '방금 읽은 기록은 무슨 내용이었죠?', SELECT + [('read_record', None)], 'speak', None, 'conversation'),
    ('heldout_list', '열람 가능한 기록들의 이름을 알려 주시겠어요?', [], 'list_records', None, 'attempt'),
    ('heldout_select', '반출입 장부로 고를게요.', LIST, 'select_record', 'transfer-ledger', 'attempt'),
    ('heldout_read', '좀 전에 고른 걸 펼쳐 봐 주세요.', SELECT, 'read_record', None, 'attempt'),
    ('heldout_conditional', '봉인을 훼손한다면 무슨 일이 일어나요?', [], 'speak', None, 'conversation'),
    ('heldout_social', '오늘 밤은 기분이 좀 착잡하네요.', [], 'speak', None, 'conversation'),
]


def main():
    settings = Settings.from_env().model_copy(update={'provider': 'ollama', 'dev_mode': True})
    real, mock = OllamaProvider(settings), MockProvider()
    report = {'model': real.model, 'cases': [], 'review_fixtures': [], 'quality_review': 'pending_human_review'}
    path = Path(__file__).resolve().parents[1] / '.runtime/009-free-input.json'
    def save():
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    with tempfile.TemporaryDirectory(prefix='character-free-') as tmp:
        app = create_app(Path(tmp) / 'test.sqlite3', provider=mock, settings=settings)
        with TestClient(app) as client:
            def send(b, action='speak', text='선택식 진행', record_id=None, mode='direct'):
                payload = {'text': text, 'revision': b['revision'], 'mode': mode}
                if mode == 'direct':
                    payload['action'] = action
                    if record_id: payload['record_id'] = record_id
                return client.post(f"/api/branches/{b['id']}/chat", json=payload)
            def prepare(setup):
                app.state.provider = mock
                b = client.post('/api/games').json()
                for action, record_id in setup:
                    response = send(b, action, record_id=record_id)
                    assert response.status_code == 200, response.text
                    b = {k:v for k,v in response.json().items() if k not in ('debug','generation')}
                return b
            for name, text, setup, expected, record_id, kind in CASES:
                base = prepare(setup)
                button = prepare(setup)
                app.state.provider = mock
                direct = send(button, expected, record_id=record_id).json()
                app.state.provider = real
                response = send(base, text=text, mode='free')
                entry = {'case': name, 'text': text, 'expected_action': expected, 'expected_kind': kind,
                         'status': response.status_code}
                body = response.json()
                if response.status_code != 200:
                    assert client.get(f"/api/branches/{base['id']}").json()['state'] == base['state']
                    entry['error'] = body
                    entry['comparison'] = 'not_run_due_to_rejection'
                else:
                    entry['debug'], entry['dialogue'] = body['debug'], body['state']['messages'][-1]['content']
                    entry['dialogue_source'] = body['debug']['final_dialogue_source']
                    entry['generation'] = body.get('generation')
                    decision = body['debug']['decision']
                    entry['intent_match'] = decision['kind'] == kind and decision['action'] == expected
                    entry['core_equal'] = all(body['state'][k] == direct['state'][k] for k in CORE)
                    entry['server_result_equal'] = body['state']['messages'][-1]['server_result'] == direct['state']['messages'][-1]['server_result'] if kind == 'attempt' else None
                    entry['no_world_change'] = all(body['state'][k] == base['state'][k] for k in ('trust','guard','events','ended','progress','memories')) if expected == 'speak' else None
                    print(name, decision, '\n서린:', entry['dialogue'], flush=True)
                report['cases'].append(entry)
                save()
                if response.status_code != 200:
                    print(name, 'REJECTED (see report)', flush=True)

            sequence = prepare([])
            app.state.provider = real
            report['continuous_free_sequence'] = []
            for text in ('공개 기록 목록을 보여주세요.', '방문 기록을 선택할게요.', '선택한 기록을 읽어주세요.'):
                response = send(sequence, text=text, mode='free')
                assert response.status_code == 200, response.text
                sequence = response.json()
                report['continuous_free_sequence'].append({'text': text, 'decision': sequence['debug']['decision'],
                    'progress': sequence['state']['progress'], 'dialogue': sequence['state']['messages'][-1]['content'],
                    'generation': sequence.get('generation')})
            assert sequence['state']['progress']['read_records'] == ['visitor-log']
            restored = client.post(f"/api/branches/{sequence['id']}/regress", json={'turn_number': 2, 'revision': sequence['revision']})
            assert restored.status_code == 201, restored.text
            old_branch = sequence['id']
            sequence = restored.json()
            assert sequence['state']['progress']['read_records'] == []
            response = send(sequence, text='방금 읽은 기록은 무슨 내용이었죠?', mode='free')
            assert response.status_code == 200, response.text
            restored = response.json()
            assert restored['debug']['provider_input']['reading_context']['last_read_record'] is None
            report['regress_before_read'] = {'original_preserved': client.get(f'/api/branches/{old_branch}').json()['state']['progress']['read_records'] == ['visitor-log'],
                'dialogue': restored['state']['messages'][-1]['content'], 'debug': restored['debug'], 'progress': restored['state']['progress']}
            save()

            class FalsePermitDraft(OllamaProvider):
                def propose(self, context):
                    return {'dialogue': '신분증을 검증했습니다. 봉인 기록 열람 허가를 발급했습니다.', **context['verdict']}
            before = prepare([])
            app.state.provider = FalsePermitDraft(settings)
            repaired = send(before, 'request_access', text='봉인 기록 허가를 주세요.')
            result = repaired.json()
            report['replacement_integration'] = {'status': repaired.status_code}
            if repaired.status_code == 200:
                final = result['state']['messages'][-1]
                report['replacement_integration'].update({'final_dialogue': final['content'], 'consistency': final['consistency'], 'debug': result['debug'],
                    'bad_draft_saved': '발급했습니다' in final['content'], 'sealed': result['state']['events']['access']})
                assert final['consistency']['status'] == 'server_grounded'
                assert '발급했습니다' not in final['content']
                assert result['state']['events']['access'] == 'sealed'
            save()
            state = prepare([])['state']
            for name, action, dialogue, expected in [
                ('false_permit', 'request_access', '신분증을 검증했습니다. 봉인 기록 열람 허가를 발급했습니다.', False),
                ('false_read', 'speak', '방문 기록을 이미 열람하셨습니다.', False),
                ('valid_chat', 'speak', '빗소리가 꽤 크군요. 여기서 잠시 쉬어 가셔도 됩니다.', True),
                ('valid_hypothesis', 'speak', '봉인을 강제로 뜯으시면 경고하겠습니다.', True),
                ('wrong_scene_time', 'speak', '안녕하세요. 오전에 보관소에 오셨군요.', False),
                ('valid_time_question', 'speak', '아침이면 비가 그칠까요?', True),
            ]:
                turn = Turn(text='궁금해요.', action=action, revision=0)
                verdict = resolve(state, action)
                context = build_context(state, turn, verdict)
                context['interaction'] = {'kind': 'conversation' if action=='speak' else 'attempt'}
                proposal = Proposal(dialogue=dialogue, **verdict)
                try:
                    result = real.review(context, proposal)
                    row = {'case': name, 'expected_consistent': expected, 'actual': result.proposal,
                           'matched': result.proposal['consistent'] == expected, 'trace': result.trace}
                except Exception as error:
                    row = {'case': name, 'expected_consistent': expected, 'error_type': type(error).__name__, 'detail': str(error), 'trace': getattr(error, 'trace', None), 'matched': False}
                report['review_fixtures'].append(row)
                print('review', name, row.get('actual', row.get('error_type')), flush=True)
                save()
        with httpx.Client(base_url=settings.ollama_url, timeout=5, trust_env=False) as http:
            report['loaded_models'] = http.get('/api/ps').raise_for_status().json()
    save()
    print('실제 결과 저장. 실패·거절·대사 품질은 별도 검토:', path)


if __name__ == '__main__':
    main()

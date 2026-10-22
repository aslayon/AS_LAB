"""Ask the same real-model question before/after reading and after DB regression.

Run from root: .venv/bin/python -m scripts.verify_record_recall
Mock prepares selected actions; Ollama generates all question responses. The
report checks state/grounding only. Review dialogue quality separately.
"""
import json
import statistics
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.world import load_world
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.providers import MockProvider
from app.settings import Settings

QUESTION = '방금 읽은 기록은 무슨 내용이었죠?'


def main():
    PUBLIC_RECORDS = load_world()['public_records']
    settings = Settings.from_env().model_copy(update={'provider': 'ollama', 'dev_mode': True})
    model, mock = OllamaProvider(settings), MockProvider()
    report = {'model': model.model, 'setup_provider': 'MockProvider', 'question_provider': 'OllamaProvider',
              'quality_review': 'pending_human_review', 'cases': []}
    output = Path(__file__).resolve().parents[1] / '.runtime/008-record-recall.json'
    def save():
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    with tempfile.TemporaryDirectory(prefix='character-recall-') as tmp:
        app = create_app(Path(tmp) / 'recall.sqlite3', provider=mock, settings=settings)
        with TestClient(app) as client:
            def send(b, action, text='선택식 진행', record_id=None, live=False, case=None):
                app.state.provider = model if live else mock
                payload = {'text': text, 'action': action, 'revision': b['revision']}
                if record_id: payload['record_id'] = record_id
                response = client.post(f"/api/branches/{b['id']}/chat", json=payload)
                if response.status_code != 200:
                    report['failure'] = {'case': case, 'status': response.status_code, 'response': response.json()}
                    save()
                    raise RuntimeError(f'{case}: {response.status_code}')
                after = response.json()
                if live:
                    assert after['state']['progress'] == b['state']['progress']
                    assert after['state']['events'] == b['state']['events']
                    assert after['state']['memories'] == b['state']['memories']
                    entry = {'case': case, 'question': text, 'state_validation': 'passed',
                             'reading_context': after['debug']['provider_input']['reading_context'],
                             'dialogue': after['state']['messages'][-1]['content'],
                             'debug': after['debug'], **after['generation']}
                    report['cases'].append(entry)
                    print(f"{case}: {entry['elapsed_ms']/1000:.2f}s\n{entry['dialogue']}", flush=True)
                return {k: v for k, v in after.items() if k not in ('debug', 'generation')}

            for record in PUBLIC_RECORDS:
                b = client.post('/api/games').json()
                b = send(b, 'list_records')
                selected = send(b, 'select_record', record_id=record['id'])
                b = send(selected, 'speak', QUESTION, live=True, case=record['id']+'/selected')
                assert report['cases'][-1]['reading_context']['last_read_record'] is None
                read = send(b, 'read_record', 'FUTURE_RECALL_LIVE_327')
                after = send(read, 'speak', QUESTION, live=True, case=record['id']+'/read')
                assert report['cases'][-1]['reading_context']['last_read_record']['content'] == record['content']
                restored = client.post(f"/api/branches/{after['id']}/regress", json={'turn_number': 2, 'revision': after['revision']}).json()
                assert restored['state'] == selected['state']
                assert client.get(f"/api/branches/{after['id']}").json()['state'] == after['state']
                send(restored, 'speak', QUESTION, live=True, case=record['id']+'/restored')
                entry = report['cases'][-1]
                assert entry['reading_context']['last_read_record'] is None
                context = json.dumps(entry['debug']['provider_input'], ensure_ascii=False)
                assert 'FUTURE_RECALL_LIVE_327' not in context and record['content'] not in context
                if record['id'] == 'visitor-log':
                    after = send(after, 'speak', '방금 문서 내용 좀 다시 설명해 줘.', live=True, case='visitor-log/paraphrase')
                    other = send(after, 'select_record', record_id='transfer-ledger')
                    send(other, 'speak', QUESTION, live=True, case='visitor-log/selected-other-unread')
                    evidence = report['cases'][-1]['reading_context']
                    assert evidence['selected_record']['id'] == 'transfer-ledger'
                    assert evidence['last_read_record']['id'] == 'visitor-log'
    times = [c['elapsed_ms'] for c in report['cases']]
    report['latency_ms'] = {'min': min(times), 'max': max(times), 'median': statistics.median(times)}
    save()
    print(f'상태·질문 근거 검증 통과. 대사 의미는 별도 수동 검토: {output}')


if __name__ == '__main__':
    main()

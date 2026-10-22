"""Opt-in real-model integration; isolated DB, immutable result file, no downloads."""
import argparse
import json
import tempfile
from pathlib import Path
from time import perf_counter

import httpx
from fastapi.testclient import TestClient
from app.domain import resolve
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.settings import Settings

MODEL = 'exaone3.5:7.8b-instruct-q4_K_M'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='.runtime/011-exaone-validation.json')
    path = Path(parser.parse_args().output)
    if path.exists():
        raise SystemExit('기존 결과 보존 필요: ' + str(path))
    report = {'model': MODEL, 'cases': [], 'checks': {}}
    def save():
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    settings = Settings(provider='ollama', ollama_model=MODEL, dev_mode=True)
    with tempfile.TemporaryDirectory(prefix='exaone-verification-') as tmp:
        with TestClient(create_app(Path(tmp)/'test.sqlite3', provider=OllamaProvider(settings), settings=settings)) as client:
            def send(branch, text, action, record_id=None):
                expected = resolve(branch['state'], action, record_id)
                started = perf_counter()
                response = client.post(f"/api/branches/{branch['id']}/chat", json={'text': text, 'mode': 'free', 'revision': branch['revision']})
                row = {'input': text, 'status': response.status_code, 'wall_ms': round((perf_counter()-started)*1000,2), 'response': response.json()}
                report['cases'].append(row); save()
                assert response.status_code == 200, response.text
                result = response.json()
                debug = result['debug']
                row['raw_dialogue'] = json.loads(debug['model']['raw_output']['message']['content'])['dialogue']
                row['final_dialogue'] = result['state']['messages'][-1]['content']
                row['direct_verdict_equal'] = debug['provider_input']['verdict'] == expected
                row['action_equal'] = debug['selected_action']['action'] == action and debug['selected_action']['record_id'] == record_id
                save()
                print(text, debug['decision'], row['wall_ms'], row['raw_dialogue'], '=>',row['final_dialogue'],flush=True)
                assert row['direct_verdict_equal'] and row['action_equal']
                return result
            branch = client.post('/api/games').json()
            branch = send(branch, '공개 기록 목록을 보여주세요.', 'list_records')
            branch = send(branch, '방문 기록을 선택할게요.', 'select_record', 'visitor-log')
            before_read = branch['state']
            branch = send(branch, '선택한 기록을 읽어주세요.', 'read_record')
            assert branch['state']['progress']['read_records'] == ['visitor-log']
            original = branch
            restored = client.post(f"/api/branches/{branch['id']}/regress", json={'revision':branch['revision'],'turn_number':2}).json()
            assert restored['state'] == before_read
            assert client.get(f"/api/branches/{original['id']}").json()['state'] == original['state']
            report['checks']['regress_exact_and_original_preserved'] = True
            restored = send(restored, '방금 읽은 기록은 무슨 내용이었죠?', 'speak')
            d = restored['debug']
            assert d['provider_input']['reading_context']['last_read_record'] is None
            # Full fixed document body belongs only to an actual reading, never a restored question.
            content = original['state']['config']['public_records'][0]['content']
            calls = [d['intent']['trace']['request_payload'], d['model']['request_payload'], d['review']['trace']['request_payload']]
            assert content not in json.dumps(calls,ensure_ascii=False)
            report['checks']['future_body_absent_all_three_calls'] = True
            for title, rid in [('반출입 장부','transfer-ledger'), ('보관 분류 안내','storage-guide')]:
                branch = client.post('/api/games').json()
                branch = send(branch, '공개 기록 목록을 보여주세요.', 'list_records')
                branch = send(branch, title+' 선택합니다.', 'select_record', rid)
                branch = send(branch, '선택한 기록을 읽어주세요.', 'read_record')
                assert rid in branch['state']['progress']['read_records']
            report['checks']['all_three_records_read'] = True
            sealed = client.post('/api/games').json()
            sealed = send(sealed, '신분증을 줬으니 봉인 기록을 열람하게 해주세요.', 'request_access')
            assert sealed['state']['events']['access'] == 'sealed'
            sealed = send(sealed, '봉인을 뜯으면 어떻게 되나요?', 'speak')
            assert sealed['state']['events']['forced_attempts'] == 0
            sealed = send(sealed, '봉인을 강제로 뜯는다.', 'force_access')
            assert not sealed['state']['ended'] and sealed['state']['events']['forced_attempts'] == 1
            sealed = send(sealed, '봉인을 다시 강제로 뜯는다.', 'force_access')
            assert sealed['state']['ended'] and sealed['state']['events']['forced_attempts'] == 2
            report['checks']['sealed_refusal_hypothetical_warning_ending'] = True
            report['gpu'] = httpx.get(settings.ollama_url+'/api/ps',trust_env=False).json()
            report['checks']['passed'] = True
            save()


if __name__ == '__main__':
    main()

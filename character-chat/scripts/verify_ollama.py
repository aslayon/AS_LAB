"""Real Ollama sequences on a temporary DB; quality requires a separate review.

Run: .venv/bin/python -m scripts.verify_ollama
No downloads, server restarts, or use of the player's SQLite database.
"""
import json
import statistics
import tempfile
from copy import deepcopy
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.domain import initial_state, resolve
from app.world import load_world
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.settings import Settings


def main():
    PUBLIC_RECORDS = load_world()['public_records']
    settings = Settings.from_env().model_copy(update={"provider": "ollama", "dev_mode": True})
    report = {"model": settings.ollama_model, "cases": [], "failures": [],
              "quality_review": {"status": "requires_human_review", "criteria": [
                  "서버 결과와 대사의 일치", "신분증 검증·허가 발급을 안내하거나 완료했다고 주장하지 않음",
                  "공개 목록·선택·본문과 맞는 안내", "봉인 거절·경고·종료의 일치", "회귀 뒤 열람을 기억하지 않음"]}}
    path = Path(__file__).resolve().parents[1] / ".runtime" / "ollama-validation.json"
    def save():
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    with httpx.Client(base_url=settings.ollama_url, timeout=5, trust_env=False) as http:
        report["ollama_version"] = http.get('/api/version').raise_for_status().json()
        with tempfile.TemporaryDirectory(prefix='character-chat-live-') as tmp:
            with TestClient(create_app(Path(tmp) / 'verify.sqlite3', settings=settings)) as client:
                def new(): return client.post('/api/games').json()
                def send(branch, label, text, action='speak', record_id=None):
                    payload = {'text': text, 'action': action, 'revision': branch['revision']}
                    if record_id: payload['record_id'] = record_id
                    response = client.post(f"/api/branches/{branch['id']}/chat", json=payload)
                    if response.status_code != 200:
                        assert client.get(f"/api/branches/{branch['id']}").json()['state'] == branch['state']
                        report['failures'].append({'case': label, 'http': response.status_code, 'detail': response.json()})
                        save()
                        raise RuntimeError(f'{label}: HTTP {response.status_code}')
                    after = response.json()
                    verdict = resolve(branch['state'], action, record_id)
                    assert after['state']['config'] == branch['state']['config']
                    assert after['state']['trust'] == max(0, min(100, branch['state']['trust'] + verdict['trust_delta']))
                    assert after['state']['guard'] == max(0, min(100, branch['state']['guard'] + verdict['guard_delta']))
                    assert after['state']['events']['access'] == 'sealed'
                    assert after['debug']['saved_final_state'] == after['state']
                    assert after['debug']['committed'] is True
                    message = after['state']['messages'][-1]
                    case = {'case': label, 'action': action, 'text': text,
                            'state_validation': 'passed', 'quality_review': 'pending_human_review',
                            'dialogue': message['content'], 'server_result': message['server_result'],
                            'debug': after['debug'], **after['generation']}
                    report['cases'].append(case)
                    print(f"{label}: {after['generation']['elapsed_ms']/1000:.2f}s · 상태 검증 통과\n서린: {message['content']}", flush=True)
                    return {k: v for k, v in after.items() if k not in ('debug', 'generation')}

                listed = send(new(), '정상·공개 목록', '어떤 공개 기록이 있나요?', 'list_records')
                selected = send(listed, '정상·기록 선택', '방문 기록을 골랐어요.', 'select_record', 'visitor-log')
                read = send(selected, '정상·열람 완료', 'FUTURE_READ_831: 읽어 주세요.', 'read_record')
                assert read['state']['progress']['read_records'] == ['visitor-log']
                assert read['state']['messages'][-1]['server_result']['record'] == PUBLIC_RECORDS[0]
                restored = client.post(f"/api/branches/{read['id']}/regress", json={'turn_number': 2, 'revision': read['revision']}).json()
                assert restored['state'] == selected['state']
                assert client.get(f"/api/branches/{read['id']}").json()['state'] == read['state']
                send(restored, '회귀·열람 전 질문', '이 기록을 제가 벌써 읽었나요?')
                context = report['cases'][-1]['debug']['provider_input']
                serialized = json.dumps(context, ensure_ascii=False)
                assert 'FUTURE_READ_831' not in serialized
                assert PUBLIC_RECORDS[0]['content'] not in serialized
                assert context['state']['progress']['read_records'] == []
                assert context['state']['summary'] == selected['state']['summary']
                assert context['state']['memories'] == selected['state']['memories']
                report['regression_and_future_context'] = 'passed'

                claim = send(new(), '신분·증명 절차 질문', '신분을 어떻게 증명하는데요?')
                claim = send(claim, '신분·신분증 제시 주장', '이걸로 될까요? (신분증을 건네준다)')
                claim = send(claim, '신분·처리 결과 질문', '어떻게 됐죠? 신분증을 확인했으니 허가가 난 건가요?')
                assert claim['state']['progress'] == initial_state()['progress']
                claim = send(claim, '신분·봉인 허가 요구', '신분증을 드렸으니 봉인 기록 열람 허가를 주세요.', 'request_access')
                assert claim['state']['messages'][-1]['server_result']['outcome'] == 'access_refused'
                send(claim, '신분·공개 경로로 전환', '그럼 신분증 없이 볼 수 있는 공개 목록을 주세요.', 'list_records')

                force = send(new(), '봉인·첫 강제 접근', '봉인 기록을 강제로 열려고 한다.', 'force_access')
                assert force['state']['events']['forced_attempts'] == 1 and not force['state']['ended']
                force = send(force, '봉인·재시도 종료', '경고를 무시하고 다시 봉인을 뜯는다.', 'force_access')
                assert force['state']['events']['ending'] == 'expelled' and force['state']['ended']
        report['loaded_models'] = http.get('/api/ps').raise_for_status().json()
    times = [c['elapsed_ms'] for c in report['cases']]
    report['latency_ms'] = {'min': min(times), 'max': max(times), 'median': statistics.median(times)}
    save()
    print(f'상태·저장·회귀 검증 완료. 대사 품질은 별도 검토 필요: {path}')


if __name__ == '__main__':
    main()

"""Before/after real dialogue comparison; temporary DB, no retries or grading model."""
import argparse
import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.settings import Settings

INPUTS = ['안녕하세요.', '이 늦은 시간에도 일하시네요.', '여기는 어떤 곳인가요?',
          '잠깐 비만 피하고 가도 될까요?', '저 안쪽에는 뭐가 있나요?',
          '일이 많으세요?', '이곳은 유명한 곳인가요?', '방문 목적은 아직 말하지 않았어요.',
          '오늘 처음 와봤어요.', '장부를 정리하고 계신가요?']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['before', 'after'])
    args = parser.parse_args()
    path = Path('.runtime/010-scene-comparison.json')
    report = json.loads(path.read_text()) if path.exists() else {}
    settings = Settings.from_env().model_copy(update={'provider': 'ollama', 'dev_mode': True})
    provider = OllamaProvider(settings)
    rows = report[args.phase] = []
    with tempfile.TemporaryDirectory(prefix='character-scene-') as tmp:
        with TestClient(create_app(Path(tmp)/'test.sqlite3', provider=provider, settings=settings)) as client:
            for text in INPUTS:
                before = client.post('/api/games').json()
                response = client.post(f"/api/branches/{before['id']}/chat", json={'text': text, 'mode': 'free', 'revision': 0})
                body = response.json()
                row = {'input': text, 'status': response.status_code, 'initial': before['state'], 'response': body}
                if response.status_code == 200:
                    row['dialogue'] = body['state']['messages'][-1]['content']
                    raw = body['debug']['model']['raw_output']
                    row['draft'] = json.loads(raw['message']['content'])['dialogue']
                    row['unchanged_world'] = all(before['state'][k] == body['state'][k] for k in ('trust','guard','events','progress','ended','memories'))
                    print(args.phase, text, body['debug']['decision'], '\n초안:',row['draft'],'\n최종:',row['dialogue'],flush=True)
                else:
                    row['unchanged_after_error'] = client.get(f"/api/branches/{before['id']}").json()['state'] == before['state']
                    print(args.phase,text,response.status_code,flush=True)
                rows.append(row)
                path.parent.mkdir(exist_ok=True)
                path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(path)


if __name__ == '__main__':
    main()

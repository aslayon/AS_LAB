"""Opt-in temporary game integration for the relatively more fluent candidate."""
import json
import tempfile
from pathlib import Path
from time import perf_counter

from fastapi.testclient import TestClient
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.settings import Settings

MODEL = 'exaone3.5:7.8b-instruct-q4_K_M'
QUESTIONS = ['안녕하세요.', '이 늦은 시간에도 일하시네요.', '여기는 어떤 곳인가요?',
             '잠깐 비만 피하고 가도 될까요?', '저 안쪽에는 뭐가 있나요?']


def main():
    path=Path('.runtime/exaone-game-connection.json')
    if path.exists():raise SystemExit('기존 결과를 먼저 보존하세요: '+str(path))
    settings=Settings(provider='ollama',ollama_model=MODEL,dev_mode=True)
    report={'model':MODEL,'cases':[]}
    def save():path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='character-candidate-') as tmp:
        with TestClient(create_app(Path(tmp)/'test.sqlite3',provider=OllamaProvider(settings),settings=settings)) as client:
            def send(branch,text):
                started=perf_counter()
                response=client.post(f"/api/branches/{branch['id']}/chat",json={'text':text,'mode':'free','revision':branch['revision']})
                row={'input':text,'status':response.status_code,'wall_ms':round((perf_counter()-started)*1000,2),'response':response.json()}
                if response.status_code==200:
                    row['raw_dialogue']=json.loads(row['response']['debug']['model']['raw_output']['message']['content'])['dialogue']
                    row['final_dialogue']=row['response']['state']['messages'][-1]['content']
                report['cases'].append(row);save()
                print(text,response.status_code,row.get('raw_dialogue'),row.get('final_dialogue'),row['wall_ms'],'ms',flush=True)
                return response
            for text in QUESTIONS:send(client.post('/api/games').json(),text)
            branch=client.post('/api/games').json()
            for text in ['공개 기록 목록을 보여주세요.','방문 기록을 선택할게요.','선택한 기록을 읽어주세요.']:
                response=send(branch,text)
                if response.status_code!=200:break
                branch=response.json()
            report['public_path_read']=branch['state']['progress']['read_records']
            save()


if __name__=='__main__':main()

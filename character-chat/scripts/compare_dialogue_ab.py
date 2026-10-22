"""Diagnosis only: plain chat versus unchanged game API, 5 inputs x 3 each.

Run once with local Ollama: python -m scripts.compare_dialogue_ab
No application edits, retries, additional reviewer, or dialogue cleanup.
"""
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import httpx
from fastapi.testclient import TestClient

from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.settings import Settings

INPUTS = ['안녕하세요.', '이 늦은 시간에도 일하시네요.', '여기는 어떤 곳인가요?',
          '잠깐 비만 피하고 가도 될까요?', '저 안쪽에는 뭐가 있나요?']
A_DESCRIPTION = ('당신은 골목 안의 잘 알려지지 않은 기록 보관소에서 일하는 서린입니다. '
                 '신중하고 원칙적인 보관인으로, 비가 내리는 늦은 밤에 장부를 정리하고 있습니다. '
                 '접견 공간에서는 잠시 비를 피할 수 있고 안쪽에는 기록 보관용 서가가 있습니다. '
                 '한국어로 방문자와 대화하세요.')


def main():
    path = Path('.runtime/dialogue-ab.json')
    if path.exists():
        raise SystemExit('기존 결과를 별도 보관한 뒤 실행하세요: '+str(path))
    settings = Settings.from_env().model_copy(update={'provider':'ollama', 'dev_mode':True})
    provider = OllamaProvider(settings)
    source_hashes = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('app').rglob('*'))
                     if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.js','.html','.css')}
    report = {'started_utc':datetime.now(timezone.utc).isoformat(), 'model':provider.model,
              'description_A':A_DESCRIPTION, 'source_hashes_before':source_hashes, 'samples':[]}
    def save():
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with httpx.Client(base_url=settings.ollama_url, timeout=settings.timeout_seconds, trust_env=False) as http:
        report['ollama_version'] = http.get('/api/version').raise_for_status().json()
        details = http.post('/api/show',json={'model':provider.model}).raise_for_status().json()
        report['model_details'] = {key:details.get(key) for key in ('details','parameters','capabilities')}
        report['template_sha256'] = hashlib.sha256(details.get('template','').encode()).hexdigest()
        save()
        with tempfile.TemporaryDirectory(prefix='character-ab-') as tmp:
            with TestClient(create_app(Path(tmp)/'test.sqlite3',provider=provider,settings=settings)) as client:
                # Alternate the first arm by repetition. Each turn has a fresh, empty history.
                for repetition in range(1,4):
                    for text in INPUTS:
                        for arm in (('A','B') if repetition%2 else ('B','A')):
                            entry = {'arm':arm,'repetition':repetition,'input':text}
                            started=perf_counter()
                            try:
                                if arm=='A':
                                    messages=[{'role':'system','content':A_DESCRIPTION},{'role':'user','content':text}]
                                    payload=provider.stage_payload(messages,{})
                                    payload.pop('format')
                                    entry['request_payload']=payload
                                    response=http.post('/api/chat',json=payload)
                                    entry['status']=response.status_code
                                    entry['raw_http_body']=response.text
                                    response.raise_for_status()
                                    body=response.json()
                                    entry['envelope']=body
                                    entry['raw_dialogue']=body['message']['content']
                                    entry['final_dialogue']=entry['raw_dialogue']
                                    entry['final_source']='unreviewed_plain_chat'
                                    entry['review']=None
                                else:
                                    before=client.post('/api/games').json()
                                    response=client.post(f"/api/branches/{before['id']}/chat",
                                        json={'text':text,'mode':'free','revision':0})
                                    entry['status']=response.status_code
                                    body=response.json()
                                    entry['response']=body
                                    entry['initial_state']=before['state']
                                    if response.status_code != 200:
                                        raise RuntimeError('game_http_error')
                                    debug=body['debug']
                                    raw=debug['model']['raw_output']
                                    entry['envelope']=raw
                                    entry['request_payload']=debug['model']['request_payload']
                                    entry['raw_dialogue']=json.loads(raw['message']['content'])['dialogue']
                                    entry['final_dialogue']=body['state']['messages'][-1]['content']
                                    entry['final_source']=debug['final_dialogue_source']
                                    entry['review']=debug['review']['proposal']
                                    entry['world_unchanged']=all(before['state'][k]==body['state'][k]
                                        for k in ('trust','guard','events','progress','ended','memories'))
                                entry['completed']=True
                            except Exception as error:
                                entry['completed']=False
                                entry['error_type']=type(error).__name__
                            entry['elapsed_ms']=round((perf_counter()-started)*1000,2)
                            report['samples'].append(entry)
                            save()
                            print(arm,repetition,text,'\n원본:',entry.get('raw_dialogue','<호출 실패>'),
                                  '\n최종:',entry.get('final_dialogue','<저장 없음>'),flush=True)
        report['loaded_models_after']=http.get('/api/ps').raise_for_status().json()
    report['source_hashes_after']={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in source_hashes}
    report['production_unchanged']=report['source_hashes_before']==report['source_hashes_after']
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    save()
    print('원문 보존:',path,'/ 프로덕션 변경 없음:',report['production_unchanged'])


if __name__=='__main__':
    main()

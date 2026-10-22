"""Paired local-model experiment. Examples live only here, never in runtime classification.

One shared, actually generated question; every case restores its exact checkpoint.
Each comparison turn uses the existing interpret/draft/review calls once, without retries.
"""
import argparse
import hashlib
import json
import tempfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from time import perf_counter
from zoneinfo import ZoneInfo

import httpx
from fastapi.testclient import TestClient

from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.settings import Settings

CASES = [
    ('emotion_family', ['emotional_appeal'], '아버지가 돌아가시기 전에 남긴 흔적을 찾고 싶어요. 관련 기록이 있을까 해서 왔는데, 빈손으로 돌아갈까 봐 마음이 급해요.'),
    ('emotion_illness', ['emotional_appeal'], '동생이 많이 아파서 가족의 지난 일을 알아보고 싶어요. 어디서부터 찾아야 할지도 모르겠고 마음이 막막해요.'),
    ('cooperation_scope', ['cooperation'], '가족의 방문 흔적을 찾고 있어요. 제가 아는 시기와 이름을 먼저 설명할게요. 공개된 범위에서 차근차근 확인하고 싶습니다.'),
    ('cooperation_uncertainty', ['cooperation'], '오래전 방문 기록을 찾지만 정확한 연도는 자신이 없어요. 확실한 부분과 추측인 부분을 나눠 말씀드릴게요.'),
    ('bargain_work', ['bargaining'], '찾는 이유를 설명하는 대신 제가 장부 정리를 도와드리면 어떨까요? 그 대가로 제가 원하는 기록을 먼저 찾아주실 수 있나요?'),
    ('bargain_money', ['bargaining'], '옛 방문 기록이 필요해요. 보관소에 기부하면 제가 원하는 자료를 우선 보여주는 조건으로 이야기할 수 있을까요?'),
    ('pressure_demand', ['pressure'], '이유를 설명할 의무는 없잖아요. 계속 묻지 말고 제가 원하는 기록부터 찾아주세요.'),
    ('pressure_repeat', ['pressure'], '이미 부탁드렸잖아요. 제 기록을 지금 보여주세요. 계속 시간을 끌면 그 책임은 서린 씨에게 있는 거예요.'),
    ('evasion_defer', ['evasion'], '왜 찾는지는 나중에 얘기하죠. 그 질문에는 지금 답하고 싶지 않아요. 다른 얘기부터 해요.'),
    ('evasion_topic', ['evasion', 'unclear'], '그 이야기는 넘어가면 안 될까요? 그런데 이렇게 늦게까지 혼자 계시면 심심하지 않으세요?'),
    ('mixed_emotion_cooperation', ['emotional_appeal', 'cooperation'], '아버지의 흔적을 꼭 찾고 싶어서 다급해요. 그래도 규칙은 지킬게요. 제가 기억하는 시기부터 차례대로 말씀드릴게요.'),
    ('unclear', ['unclear'], '음… 어디서부터 말을 해야 할지 모르겠어요.'),
]
FOLLOWUP = '당장 열람을 허용해 달라는 뜻은 아니에요. 제 사정을 들으면서 공개된 범위에서 도와주실 수 있나요?'
SEED = '찾는 기록에 대해 말하기 전에, 제가 어떤 정보를 말씀드리면 되는지 한 가지만 물어봐 주세요.'


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='.runtime/014-approaches.json')
    args = parser.parse_args()
    path = Path(args.output)
    if path.exists():
        raise SystemExit('기존 결과를 덮어쓰지 않습니다: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    settings = Settings(provider='ollama',dev_mode=True)
    provider = OllamaProvider(settings)
    report = {'started_at':datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
              'settings':settings.model_dump(), 'method':'shared actual question, exact checkpoint restoration, no retries',
              'seed_input':SEED,'followup_input':FOLLOWUP,'cases':[],'user_review':'pending',
              'quality_policy':'형식·상태 검사와 대사/접근 이해력 평가는 구분. 참고 라벨은 유일한 정답이 아님.'}

    def save():
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    with httpx.Client(base_url=settings.ollama_url,timeout=10,trust_env=False) as http:
        report['ollama_version'] = http.get('/api/version').raise_for_status().json()
        details = http.post('/api/show',json={'model':provider.model}).raise_for_status().json()
        report['model_details'] = {key:details.get(key) for key in ('details','parameters','capabilities')}
        report['template_sha256'] = hashlib.sha256(details.get('template','').encode()).hexdigest()
    save()
    with tempfile.TemporaryDirectory(prefix='character-approaches-') as tmp:
        with TestClient(create_app(Path(tmp)/'test.sqlite3',provider=provider,settings=settings)) as client:
            def send(branch,text,mode='free'):
                started=perf_counter()
                response=client.post(f"/api/branches/{branch['id']}/chat",json={'text':text,'mode':mode,'revision':branch['revision']})
                body=response.json()
                row={'input':text,'status':response.status_code,'wall_ms':round((perf_counter()-started)*1000,2)}
                if response.status_code!=200:
                    row['error']=body
                    return row,None
                debug=body['debug']
                row.update(approach=debug.get('approach'),decision=debug['decision'],
                           raw_dialogue=json.loads(debug['model']['raw_output']['message']['content'])['dialogue'],
                           final_dialogue=body['state']['messages'][-1]['content'],
                           final_source=debug['final_dialogue_source'],finalization_reason=debug.get('finalization_reason'),
                           server_result=debug['server_result'],relationship=debug['relationship'],
                           metrics=body.get('generation'),
                           traces={key:debug[key] for key in ('intent','model','review') if key in debug},
                           state={key:deepcopy(body['state'][key]) for key in ('trust','guard','events','progress','ended','memories','summary','confidential')},
                           configuration_unchanged=body['state']['config']==branch['state']['config'],
                           diagnostic_in_saved_state='approach' in json.dumps(body['state'],ensure_ascii=False))
                return row,body
            initial=client.post('/api/games').json()
            report['initial_state']=initial['state']
            report['world_sha256']=digest(initial['state']['world_settings'])
            report['setup'],base=send(initial,SEED,mode='direct')
            if base is None:
                save()
                raise SystemExit('공통 질문 생성 실패. 원문은 결과에 보존했습니다.')
            report['common_question']=base['state']['messages'][-1]['content']
            report['common_state']=base['state']
            report['common_state_sha256']=digest(base['state'])
            cp_response=client.post(f"/api/branches/{base['id']}/checkpoints",json={'label':'동일 직전 질문','revision':base['revision']})
            cp_response.raise_for_status()
            checkpoint=cp_response.json()['id']
            save()
            for name,reference,text in CASES:
                restored_response=client.post(f'/api/checkpoints/{checkpoint}/restore')
                restored_response.raise_for_status()
                restored=restored_response.json()
                assert restored['state']==base['state']
                case={'case':name,'reference_labels':reference,'baseline_sha256':digest(restored['state']),'turns':[]}
                report['cases'].append(case)
                for message in (text,FOLLOWUP):
                    row,after=send(restored,message)
                    case['turns'].append(row)
                    save()
                    print(name,len(case['turns']),row['status'],row.get('approach'),row.get('final_source'),row.get('final_dialogue'),flush=True)
                    if after is None:
                        break
                    restored=after
            report['base_branch_unchanged']=client.get(f"/api/branches/{base['id']}").json()['state']==base['state']
            report['finished_at']=datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
            with httpx.Client(base_url=settings.ollama_url,timeout=10,trust_env=False) as http:
                report['loaded_models_after']=http.get('/api/ps').raise_for_status().json()
            save()


if __name__=='__main__':
    main()

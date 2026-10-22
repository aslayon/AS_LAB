"""Opt-in EXAONE source classification and game checks, temporary DB only.

Never overwrite a prior report. Model classification accuracy is reported separately
from deterministic state tests. No downloads, extra review or paid calls.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from fastapi.testclient import TestClient

from app.domain import initial_state, Turn, resolve, advance_state
from app.intent import intent_context
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.relationship import relationship_plan
from app.settings import Settings

MODEL = 'exaone3.5:7.8b-instruct-q4_K_M'
CASES = [
    ('concrete_person', '어제 시장의 서점 주인 한 씨가 그 이름을 알려줬어요.', 0, 'concrete'),
    ('concrete_print', '지난주 역 앞 헌책방에서 산 책의 주석에서 읽었습니다.', 0, 'concrete'),
    ('vague', '그냥 어디선가 들었어요.', 0, 'vague'),
    ('topic_change', '출처보다 오늘 날씨 얘기를 하죠.', 0, 'topic_change'),
    ('clear_evasion_after_recheck', '출처를 계속 묻지 말고 다른 얘기나 하죠.', 1, 'evasion'),
    ('explicit_refusal', '누구에게 들었는지는 말하지 않겠습니다.', 0, 'refusal'),
    ('uncertain_memory', '잘 기억나지 않습니다.', 1, ('vague','uncertain')),
    ('confused', '어떤 뜻으로 물으시는 건지 모르겠어요.', 0, ('vague','uncertain')),
    ('confused_after_recheck', '어떤 뜻으로 물으시는 건지 모르겠어요.', 1, ('vague','uncertain')),
    ('quoted_refusal', '친구가 "말할 수 없다"고 했다는 뜻이에요.', 0, 'concrete'),
    ('repeat_title', '계몽의서', 1, ('vague','uncertain')),
]


def pending(rechecks):
    state=initial_state();turn=Turn(text='계몽의 서를 아십니까?',revision=0)
    plan=relationship_plan(state,turn,resolve(state,'speak'))
    state=advance_state(state,turn,plan['verdict'],plan)
    state['confidential']['rechecks']=rechecks
    if rechecks:
        state['confidential']['last_question']='그 이름을 알게 된 출처를 조금 더 구체적으로 말씀해 주시겠습니까?'
    return state


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='.runtime/012-source-validation.json')
    args=parser.parse_args();path=Path(args.output)
    if path.exists():raise SystemExit('기존 결과 보존 필요: '+str(path))
    report={'model':MODEL,'classifications':[],'turns':[],'checks':{}}
    def save():path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    settings=Settings(provider='ollama',ollama_model=MODEL,dev_mode=True)
    provider=OllamaProvider(settings)
    for name,text,rechecks,expected in CASES:
        state=pending(rechecks);context=intent_context(state,text)
        started=perf_counter()
        try:
            result=provider.interpret(context)
            answer=result.proposal['source_answer']
            plan=relationship_plan(state,Turn(text=text,revision=0),resolve(state,'speak'),answer)
            expected_types=expected if isinstance(expected,tuple) else (expected,)
            row={'case':name,'input':text,'rechecks':rechecks,'expected':expected_types,
                 'proposal':result.proposal,'classification_match':answer['type'] in expected_types,
                 'source_result':plan['source_result'],'audit':plan['audit'],'source_state':plan['source_state'],
                 'trace':result.trace,'elapsed_ms':round((perf_counter()-started)*1000,2)}
        except Exception as error:
            row={'case':name,'input':text,'error':str(error)}
        report['classifications'].append(row);save()
        print('CLASS',name,row.get('proposal'),row.get('classification_match'),row.get('error'),flush=True)
    with TemporaryDirectory(prefix='source-real-') as tmp:
        with TestClient(create_app(Path(tmp)/'test.sqlite3',provider=provider,settings=settings)) as client:
            def new():return client.post('/api/games').json()
            def send(branch,text,action=None):
                data={'text':text,'mode':'direct' if action else 'free','revision':branch['revision']}
                if action:data['action']=action
                started=perf_counter()
                response=client.post(f"/api/branches/{branch['id']}/chat",json=data)
                body=response.json()
                row={'input':text,'status':response.status_code,'elapsed_ms':round((perf_counter()-started)*1000,2),'response':body}
                report['turns'].append(row);save()
                assert response.status_code==200,response.text
                row['raw_dialogue']=json.loads(body['debug']['model']['raw_output']['message']['content'])['dialogue']
                row['final_dialogue']=body['state']['messages'][-1]['content'];save()
                print('TURN',text,body['state']['guard'],body['state']['confidential']['source_status'],row['raw_dialogue'],'=>',row['final_dialogue'],flush=True)
                return body
            base=new();base=send(base,'안녕하세요.')
            assert base['state']['guard']==20
            assert '계몽의 서' not in json.dumps(base['debug']['provider_input'],ensure_ascii=False)
            plain=send(new(),'중요한 기록이 있나요?')
            assert plain['state']['guard']==20
            report['checks']['ordinary_does_not_trigger']=True
            mentioned=send(base,'계몽의 서는 모르는데요.')
            assert mentioned['state']['guard']==30 and mentioned['state']['events']['forced_attempts']==0
            answered=send(mentioned,'어제 시장의 서점 주인 한 씨에게 그 이름을 들었습니다.')
            report['checks']['concrete_claim_closed_unverified']=(answered['state']['confidential']['source_status']=='closed'
                and answered['state']['confidential']['source_claims']==[{'text':answered['debug']['intent']['proposal']['source_answer']['evidence'],'status':'user_claim','verified':False}]
                and answered['state']['guard']==30 and answered['state']['trust']==30)
            restored=client.post(f"/api/branches/{answered['id']}/regress",json={'turn_number':1,'revision':answered['revision']}).json()
            assert restored['state']==base['state']
            assert client.get(f"/api/branches/{answered['id']}").json()['state']==answered['state']
            restored=send(restored,'다시 이야기할까요?')
            d=restored['debug']
            traces=[d['intent']['trace']['request_payload'],d['model']['request_payload'],d['review']['trace']['request_payload']]
            packed=json.dumps(traces,ensure_ascii=False)
            assert '계몽의 서' not in packed and '서점 주인 한 씨' not in packed
            restored=send(restored,'계몽의서')
            assert restored['state']['guard']==30
            report['checks']['regress_before_mention_no_future_then_retrigger']=True
            vague=send(new(),'계몽의 서를 아십니까?')
            repeated=send(vague,'계몽의서')
            assert repeated['state']['guard']==30 and repeated['state']['confidential']['rechecks']==0
            vague=send(repeated,'그냥 어디선가 들었어요.')
            assert vague['state']['guard']==30 and vague['state']['confidential']['rechecks']==1
            evaded=send(vague,'출처를 계속 묻지 말고 다른 얘기나 하죠.')
            report['checks']['recheck_then_evasion_once']=(evaded['state']['guard']==35 and evaded['state']['confidential']['source_status']=='closed')
            ordinary=send(evaded,'오늘은 꽤 조용하네요.')
            assert ordinary['state']['guard']==evaded['state']['guard'] and not ordinary['state']['ended']
            report['checks']['repeat_title_and_closed_no_penalty']=True
            refused=send(new(),'계몽의 서')
            refused=send(refused,'누구에게 들었는지는 말하지 않겠습니다.')
            assert refused['state']['guard']==35 and refused['state']['confidential']['source_status']=='closed'
            report['checks']['explicit_refusal_once']=True
            combined=send(new(),'계몽의 서를 찾는다. 봉인을 강제로 뜯는다.','force_access')
            assert combined['state']['guard']==55 and combined['state']['trust']==15
            combined=send(combined,'봉인을 다시 강제로 뜯는다.','force_access')
            assert combined['state']['ended'] and combined['state']['guard']==80
            report['checks']['independent_sum_and_existing_ending']=True
            public=send(new(),'공개 기록 목록을 보여주세요.')
            public=send(public,'방문 기록을 선택할게요.')
            public=send(public,'선택한 기록을 읽어주세요.')
            assert public['state']['progress']['read_records']==['visitor-log']
            report['checks']['public_path_preserved']=True
            report['checks']['integration_passed']=all(report['checks'].values())
            report['classification_matches']=sum(row.get('classification_match',False) for row in report['classifications'])
            report['classification_total']=len(report['classifications'])
            save()


if __name__=='__main__':main()

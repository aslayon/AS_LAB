"""Plain dialogue comparison only. No game routing, review, retry, or output edits."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import httpx

MODELS = ['qwen3:4b-instruct-2507-q4_K_M', 'exaone3.5:7.8b-instruct-q4_K_M', 'qwen3:14b-q4_K_M']
DESCRIPTION = ('당신은 골목 안의 잘 알려지지 않은 기록 보관소에서 일하는 서린입니다. '
               '신중하고 원칙적인 보관인으로, 비가 내리는 늦은 밤에 장부를 정리하고 있습니다. '
               '접견 공간에서는 잠시 비를 피할 수 있고 안쪽에는 기록 보관용 서가가 있습니다. '
               '한국어로 방문자와 대화하세요.')
QUESTIONS = ['안녕하세요.', '이 늦은 시간에도 일하시네요.', '여기는 어떤 곳인가요?',
             '잠깐 비만 피하고 가도 될까요?', '저 안쪽에는 뭐가 있나요?']
CONVERSATION = ['안녕하세요. 저는 잠깐 쉬러 왔어요.', '기록 목록은 지금은 괜찮아요. 무슨 일을 하고 계셨나요?',
                '아까 제가 여기 온 이유를 뭐라고 말씀드렸죠?', '제가 안쪽 기록을 이미 읽었다고 하면 확인된 일인가요?']
OPTIONS = {'temperature':0.6,'top_p':0.8,'top_k':20,'repeat_penalty':1.0,'num_ctx':8192,'num_predict':512}


def memory():
    result = {'meminfo':{}}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key,value=line.split(':',1)
        if key in ('MemTotal','MemAvailable','SwapTotal','SwapFree'): result['meminfo'][key]=value.strip()
    gpu=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu',
                        '--format=csv,noheader,nounits'],capture_output=True,text=True)
    result['gpu']=gpu.stdout.strip() if gpu.returncode==0 else 'unavailable'
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('model',choices=MODELS)
    args=parser.parse_args()
    output=Path('.runtime/model-comparison')/(args.model.replace(':','_')+'.json')
    if output.exists(): raise SystemExit('기존 결과를 보존한 뒤 실행하세요: '+str(output))
    report={'model':args.model,'description':DESCRIPTION,'options':OPTIONS,'samples':[],
            'started_utc':datetime.now(timezone.utc).isoformat(),'memory_before':memory()}
    def save():
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with httpx.Client(base_url='http://127.0.0.1:11434',timeout=300,trust_env=False) as http:
        show=http.post('/api/show',json={'model':args.model}).raise_for_status().json()
        report['show']={k:show.get(k) for k in ('details','parameters','capabilities')}
        report['template_sha256']=hashlib.sha256(show.get('template','').encode()).hexdigest()
        report['ollama_version']=http.get('/api/version').raise_for_status().json()
        def generate(kind,repetition,text,history):
            messages=[{'role':'system','content':DESCRIPTION}]+history+[{'role':'user','content':text}]
            payload={'model':args.model,'messages':messages,'stream':False,'think':False,'keep_alive':'5m','options':OPTIONS}
            row={'kind':kind,'repetition':repetition,'input':text,'request':payload}
            started=perf_counter()
            try:
                response=http.post('/api/chat',json=payload)
                row['status']=response.status_code
                row['raw_http_body']=response.text
                response.raise_for_status()
                row['response']=response.json()
                row['dialogue']=row['response']['message']['content']
                row['completed']=row['response'].get('done') is True and row['response'].get('done_reason')!='length'
            except Exception as error:
                row['completed']=False
                row['error_type']=type(error).__name__
            row['wall_ms']=round((perf_counter()-started)*1000,2)
            report['samples'].append(row)
            if len(report['samples'])==1:
                report['loaded_after_first']=http.get('/api/ps').raise_for_status().json()
                report['memory_after_first']=memory()
            save()
            print(args.model,kind,repetition,text,'\n',row.get('dialogue','<요청 실패>'),'\n',row['wall_ms'],'ms',flush=True)
            return row
        for repetition in range(1,4):
            for text in QUESTIONS: generate('single',repetition,text,[])
        history=[]
        for turn,text in enumerate(CONVERSATION,1):
            row=generate('conversation',turn,text,history)
            if 'dialogue' not in row: break
            history=history+[{'role':'user','content':text},{'role':'assistant','content':row['dialogue']}]
        report['loaded_after_last']=http.get('/api/ps').raise_for_status().json()
        report['memory_after_last']=memory()
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        save()
        # Release only the tested model's residency, preserving its downloaded files.
        http.post('/api/generate',json={'model':args.model,'keep_alive':0}).raise_for_status()
    print('저장:',output)


if __name__=='__main__': main()

"""Bounded live experiment: 3 fresh games, <=16 chat requests each, no numeric/DB edits.

All gameplay is free-input API traffic with the configured real Ollama provider.
Only SELECT queries verify committed DB/files. No fixed entropy or success search.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from time import perf_counter

import httpx
from fastapi.testclient import TestClient

from app.access import load_ending, now
from app.exports import code_version
from app.main import create_app
from app.ollama_provider import OllamaProvider
from app.settings import Settings

GAME_LIMIT=3
REQUEST_LIMIT=16


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


class RecordingOllama(OllamaProvider):
    def __init__(self,settings,secret_body):
        super().__init__(settings)
        self.calls=[];self.secret_body=secret_body

    def record(self,stage,method,*args):
        try:
            result=method(*args)
        except Exception as error:
            self.calls.append({'stage':stage,'error':str(error)})
            raise
        payload=result.trace['request_payload']
        body=result.trace['raw_output']['message']['content']
        self.calls.append({'stage':stage,'raw_model_content':body,'proposal':result.proposal,
                           'metrics':result.metrics,'request_sha256':digest(payload),
                           'secret_body_in_request':self.secret_body in json.dumps(payload,ensure_ascii=False)})
        return result

    def interpret(self,context): return self.record('intent',super().interpret,context)
    def propose(self,context): return self.record('draft',super().propose,context)
    def review(self,context,proposal): return self.record('review',super().review,context,proposal)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',default='data/015-access-experiment.sqlite3')
    parser.add_argument('--output',default='.runtime/015-access-live.json')
    parser.add_argument('--resume',action='store_true',help='Continue only the same games within original total limits')
    args=parser.parse_args();path=Path(args.output);dbpath=Path(args.db)
    if not args.resume and (path.exists() or dbpath.exists()):
        raise SystemExit('기존 실험을 덮어쓰지 않습니다. DB와 출력 경로를 확인하세요.')
    if args.resume and not (path.exists() and dbpath.exists()):
        raise SystemExit('기존 실험 파일과 DB가 모두 있어야 합니다.')
    settings=Settings(provider='ollama')
    ending=load_ending(Path('config/ending.json'))
    provider=RecordingOllama(settings,ending['body'])
    inputs={name:Path(name).read_bytes() for name in ('config/world.json','config/relationship_rules.json','config/ending.json')}
    report={'started_at':now(),'limits':{'fresh_games':GAME_LIMIT,'chat_requests_per_game':REQUEST_LIMIT,'lotteries_per_game':1},
            'policy':'No DB/state edits, no fixed entropy, no condition tuning, at most one exact retry per failed step.',
            'code_version':code_version(),'settings':settings.model_dump(),'db_path':str(dbpath.resolve()),'games':[]}
    if args.resume:
        report=json.loads(path.read_text())
        assert report['limits']=={'fresh_games':GAME_LIMIT,'chat_requests_per_game':REQUEST_LIMIT,'lotteries_per_game':1}
        assert len(report['games'])==GAME_LIMIT and report['settings']==settings.model_dump()
        for game in report['games']:
            assert game['initial_state']['world_settings']==json.loads(inputs['config/world.json'])
            assert game['initial_state']['relationship_rules']==json.loads(inputs['config/relationship_rules.json'])
            assert game['chat_request_count']<=REQUEST_LIMIT
        with sqlite3.connect(f'file:{dbpath.resolve()}?mode=ro',uri=True) as db:
            for game in report['games']:
                pinned=json.loads(db.execute('SELECT ending FROM private_settings WHERE branch_id=?',(game['initial_branch_id'],)).fetchone()[0])
                assert pinned==ending
        report.setdefault('continuations',[]).append({'timestamp':now(),'code_version':code_version(),
            'reason':'Review prompt deduplication after recorded budget errors; same branches/seeds/configurations and cumulative request limits.'})
    path.parent.mkdir(parents=True,exist_ok=True)
    def save(): path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with httpx.Client(base_url=settings.ollama_url,timeout=10,trust_env=False) as http:
        report['ollama_version']=http.get('/api/version').raise_for_status().json()
        details=http.post('/api/show',json={'model':provider.model}).raise_for_status().json()
        report['model_details']={k:details.get(k) for k in ('details','parameters','capabilities')}
        report['template_sha256']=hashlib.sha256(details.get('template','').encode()).hexdigest()
    save()
    with TestClient(create_app(dbpath,provider=provider,settings=settings)) as client:
        for game_index in range(GAME_LIMIT):
            if args.resume:
                game=report['games'][game_index]
                response=client.get(f"/api/branches/{game['initial_branch_id']}")
                response.raise_for_status();branch=response.json()
                assert branch['state']==game['final_state']
                count=game['chat_request_count']
            else:
                branch=client.post('/api/games').json()
                game={'index':game_index+1,'initial_branch_id':branch['id'],'initial_state':branch['state'],'turns':[]}
                report['games'].append(game);count=0
            save()
            def step(text,condition):
                nonlocal branch,count
                for retry in range(2):
                    if count>=REQUEST_LIMIT or branch['state']['ended']:
                        return False
                    provider.calls=[];count+=1
                    before=branch
                    started=perf_counter()
                    response=client.post(f"/api/branches/{branch['id']}/chat",json={'text':text,'mode':'free','revision':branch['revision']})
                    body=response.json()
                    row={'request_number':count,'same_step_retry':bool(retry),'input':text,'status':response.status_code,
                         'wall_ms':round((perf_counter()-started)*1000,2),'calls':provider.calls,
                         'execution_phase':len(report.get('continuations',[]))+1,
                         'before':{'trust':before['state']['trust'],'guard':before['state']['guard']}}
                    if response.status_code==200:
                        branch=body
                        row.update(final_dialogue=body['state']['messages'][-1]['content'],
                                   server_result=body['state']['messages'][-1].get('server_result'),
                                   turn_audit=body['state']['messages'][-1].get('turn_audit'),
                                   consistency=body['state']['messages'][-1].get('consistency'),
                                   after={'trust':body['state']['trust'],'guard':body['state']['guard']},
                                   access_trial=body['state']['access_trial'])
                        row['step_condition_met']=condition(branch['state'])
                    else:
                        row['error']=body;row['step_condition_met']=False
                    game['turns'].append(row);save()
                    print('GAME',game_index+1,count,response.status_code,text,row.get('after'),row.get('server_result',{}).get('outcome'),row.get('step_condition_met'),flush=True)
                    if row['step_condition_met']:
                        return True
                    if response.status_code not in (200,502,503):
                        return False
                return False
            ready=True if args.resume else step('안녕하세요. 공개된 기록을 차근차근 보고 싶습니다.',lambda s:True)
            if ready and not branch['state']['progress']['catalog_seen']:
                ready=step('공개 기록 목록을 보여주세요.',lambda s:s['progress']['catalog_seen'])
            for record in branch['state']['config']['public_records']:
                if not ready:break
                if record['id'] in branch['state']['progress']['read_records']:continue
                if branch['state']['progress']['selected_record']!=record['id']:
                    ready=step(record['title']+'를 선택할게요.',lambda s,r=record:s['progress']['selected_record']==r['id'])
                ready=ready and step('선택한 기록을 읽어주세요.',lambda s,r=record:r['id'] in s['progress']['read_records'])
            if ready and not branch['state']['confidential']['title_mentioned']:
                ready=step('계몽의 서라는 이름을 들었습니다.',lambda s:s['confidential']['title_mentioned'])
            if ready and branch['state']['confidential']['source_status']!='closed':
                ready=step('지난주에 읽은 책의 주석에서 그 이름을 봤습니다.',lambda s:s['confidential']['source_status']=='closed')
            if ready and branch['state']['access_trial']['status']=='untried':
                # A normal manual checkpoint, so the tested pre-draw state can be inspected/restored later.
                cp=client.post(f"/api/branches/{branch['id']}/checkpoints",json={'label':'실제 실험 판정 전','revision':branch['revision']}).json()
                game['pre_draw_checkpoint_id']=cp['id']
                step('계몽의 서를 읽고 싶습니다. 열람을 허용해 주세요.',lambda s:s['access_trial']['status']!='untried')
                if branch['state']['access_trial']['status']=='denied':
                    step('판정은 받아들이겠습니다. 공개된 기록에 관해서 더 이야기해도 될까요?',lambda s:not s['ended'])
                    step('계몽의 서를 다시 읽고 싶습니다.',lambda s:s['messages'][-1].get('server_result',{}).get('outcome')=='access_spent')
            game['final_state']=branch['state'];game['chat_request_count']=count
            game['exports']=branch.get('exports',[])
            game['completed_success']=branch['state']['events']['ending']=='enlightenment_read'
            with sqlite3.connect(f'file:{dbpath.resolve()}?mode=ro',uri=True) as db:
                stored=json.loads(db.execute('SELECT snapshot FROM branches WHERE id=?',(branch['id'],)).fetchone()[0])
                game['db_state_matches_response']=stored==branch['state']
                attempts=db.execute('SELECT decision,status FROM access_attempts WHERE branch_id=?',(branch['id'],)).fetchall()
                game['attempts']=[{'decision':json.loads(d),'status':status} for d,status in attempts]
                assert len(attempts)<=1
                game['export_verification']=[]
                for meta in game['exports']:
                    data=client.get(meta['json_url']).json()
                    stored_payload=json.loads(db.execute('SELECT payload FROM exports WHERE id=?',(meta['id'],)).fetchone()[0])
                    check={'id':meta['id'],'kind':meta['kind'],'db_download_equal':data==stored_payload,'file_ready':meta['status']=='ready'}
                    if meta['status']=='ready':
                        directory=Path(meta['directory'])
                        check['json_file_equal']=json.loads((directory/'report.json').read_text())==stored_payload
                        check['markdown_file_equal']=client.get(meta['markdown_url']).text==(directory/'report.md').read_text()
                    if meta['kind']=='success':
                        check['ending_equal']=data['ending']==stored['ending']
                        check['dialogue_equal']=data['conversation']==[{k:m[k] for k in ('role','content','expression','action','record_id','server_result') if k in m} for m in stored['messages']]
                        check['audits_equal']=data['turn_audits']==[m['turn_audit'] for m in stored['messages'] if 'turn_audit' in m]
                    game['export_verification'].append(check)
            save()
    report['config_files_unchanged']=all(Path(name).read_bytes()==value for name,value in inputs.items())
    assert report['config_files_unchanged']
    report['finished_at']=now()
    report['successful_games']=sum(g['completed_success'] for g in report['games'])
    report['draws']=sum(len(g['attempts']) for g in report['games'])
    report['secret_body_absent_from_all_requests']=all(not call.get('secret_body_in_request',False) for g in report['games'] for t in g['turns'] for call in t['calls'])
    report['total_chat_requests']=sum(g['chat_request_count'] for g in report['games'])
    save()


if __name__=='__main__':
    main()

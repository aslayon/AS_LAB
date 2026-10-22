"""DB-backed immutable report outbox. Files are expendable; game results are not."""
import hashlib
import json
import subprocess
from pathlib import Path

from .store import encode, new_id


def code_version():
    root=Path(__file__).resolve().parents[1]
    try:
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,stderr=subprocess.DEVNULL,text=True).strip()
        dirty=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=root,text=True))
    except (OSError,subprocess.SubprocessError):
        head,dirty=None,None
    digest=hashlib.sha256()
    files=sorted(list((root/'app').rglob('*.py'))+list((root/'app/static').glob('*'))+list((root/'config').glob('*.json')))
    for path in files:
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode());digest.update(path.read_bytes())
    return {'git_commit':head,'tracked_worktree_dirty':dirty,'runtime_and_configuration_sha256':digest.hexdigest()}


def queue_report(db, branch, state, attempt, phase, model, code, kind='experiment'):
    parent=None
    if branch['parent_checkpoint_id']:
        row=db.execute('SELECT branch_id FROM checkpoints WHERE id=?',(branch['parent_checkpoint_id'],)).fetchone()
        parent=row['branch_id'] if row else None
    decision=json.loads(attempt['decision'])
    conversation=[]
    turn_audits=[]
    for message in state['messages']:
        conversation.append({k:message[k] for k in ('role','content','expression','action','record_id','server_result') if k in message})
        if 'turn_audit' in message:
            turn_audits.append(message['turn_audit'])
    payload={'schema_version':'success-report-1','kind':kind,'phase':phase,
             'game_id':branch['game_id'],'branch_id':branch['id'],
             'parent_branch_id':parent,'parent_checkpoint_id':branch['parent_checkpoint_id'],
             'timestamp':decision['timestamp'],'code_version':code,'model':model,
             'world_settings':state.get('world_settings',state['config']),
             'effective_configuration':state['config'],'relationship_rules':state.get('relationship_rules'),
             'conversation':conversation,'turn_audits':turn_audits,
             'decision':decision,'request':json.loads(attempt['request_json']),
             'state':{k:state.get(k) for k in ('trust','guard','events','progress','ended','access_trial')},
             'ending':state.get('ending') if phase=='committed' else None}
    eid=new_id()
    db.execute('INSERT INTO exports(id,branch_id,attempt_id,kind,payload) VALUES(?,?,?,?,?)',
               (eid,branch['id'],attempt['id'],kind,encode(payload)))
    return eid


def markdown(payload):
    d=payload['decision'];m=payload['model']
    lines=['# 봉인 열람 '+('성공 기록' if payload['kind']=='success' else '실험 기록'),'',
           f"- 게임: {payload['game_id']}",f"- 분기: {payload['branch_id']}",
           f"- 부모 분기: {payload['parent_branch_id']}",f"- 회귀 지점: {payload['parent_checkpoint_id']}",
           f"- 판정 시각: {payload['timestamp']}",f"- 단계: {payload['phase']}",
           f"- 모델: {m['provider']} / {m['model']}",
           f"- 코드: {json.dumps(payload['code_version'],ensure_ascii=False)}",'',
           '## 판정','',f"- 판정 전 신뢰/경계: {d['before']['trust']}/{d['before']['guard']}",
           f"- 성공 확률: {d['probability']:.6f}",f"- 추첨값: {d['draw']:.17g}",
           f"- 추첨 결과: {'성공' if d['success'] else '실패'}",f"- 시도 ID: {d['id']}",
           '- reserved는 판정 예약이며 열람 완료가 아닙니다. committed와 결말을 함께 확인하세요.','',
           '## 배경·관계 실제 적용값','','```json',json.dumps({k:payload[k] for k in ('world_settings','effective_configuration','relationship_rules')},ensure_ascii=False,indent=2),'```','',
           '## 대화 원문','']
    for i,message in enumerate(payload['conversation']):
        lines.extend([f"### {i} · {'사용자 (주장·시도)' if message['role']=='user' else '서린'}",'',
                      '> '+message['content'].replace('\n','\n> '),''])
        if 'server_result' in message:
            lines.extend(['서버 결과: '+json.dumps(message['server_result'],ensure_ascii=False),''])
    lines.extend(['## 턴별 관계 변화와 근거','','```json',json.dumps(payload['turn_audits'],ensure_ascii=False,indent=2),'```','',
                  '## 공개된 결말',''])
    if payload['ending']:
        lines.extend([payload['ending']['title'],'',payload['ending']['body'],''])
    else:
        lines.extend(['공개되지 않음.',''])
    return '\n'.join(lines)


class Exporter:
    def __init__(self,store,directory):
        self.store=store;self.directory=Path(directory).resolve()

    def publish(self,branch_id,force=False):
        with self.store.connect() as db:
            rows=[dict(r) for r in db.execute('SELECT * FROM exports WHERE branch_id=?',(branch_id,))
                  if force or r['status']!='ready' or not r['directory'] or
                  not all((Path(r['directory'])/name).is_file() for name in ('report.json','report.md'))]
        for row in rows:
            try:
                # A fresh directory on every publication attempt: partial writes,
                # crashes and concurrent retries never overwrite an earlier file.
                target=self.directory/(row['id']+'-'+new_id())
                target.mkdir(parents=True,exist_ok=False)
                payload=json.loads(row['payload'])
                with (target/'report.json').open('x',encoding='utf-8') as file:
                    file.write(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
                with (target/'report.md').open('x',encoding='utf-8') as file:
                    file.write(markdown(payload))
                with self.store.connect(write=True) as db:
                    db.execute("UPDATE exports SET status='ready',directory=?,error=NULL WHERE id=?",(str(target),row['id']))
            except OSError as error:
                with self.store.connect(write=True) as db:
                    db.execute("UPDATE exports SET status='error',error=? WHERE id=?",(f'{type(error).__name__}: {error}',row['id']))

    def metadata(self,branch_id):
        with self.store.connect() as db:
            return [{**dict(row),'json_url':f"/api/exports/{row['id']}/json",'markdown_url':f"/api/exports/{row['id']}/markdown"}
                    for row in db.execute('SELECT id,kind,status,directory,error FROM exports WHERE branch_id=? ORDER BY rowid',(branch_id,))]

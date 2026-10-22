"""Server-owned, branch-scoped lottery. Private seeds survive failed turn transactions."""
import hashlib
import hmac
import json
import secrets
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from .relationship import StrictModel
from .configuration import load_configuration
from .store import encode, new_id


class Ending(StrictModel):
    version: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=20000)

    @model_validator(mode='after')
    def nonblank(self):
        if not all(v.strip() for v in (self.version,self.title,self.body)):
            raise ValueError('version/title/body에는 공백 외의 내용이 필요합니다')
        return self


def load_ending(path):
    return load_configuration(path,lambda value:Ending.model_validate(value).model_dump(),'결말')


def now():
    return datetime.now(ZoneInfo('Asia/Seoul')).isoformat()


def request_hash(request):
    return hashlib.sha256(encode(request.model_dump()).encode()).hexdigest()


def private_settings(db, branch_id, ending, seed_factory=None):
    seed=(seed_factory or (lambda:secrets.token_hex(32)))()
    if not isinstance(seed,str) or len(seed)!=64:
        raise ValueError('server seed must be 32 hex bytes')
    bytes.fromhex(seed)
    db.execute('INSERT INTO private_settings(branch_id,ending,seed) VALUES(?,?,?)',
               (branch_id,encode(ending),seed))


def copy_private_settings(db, source_id, new_id, seed_factory=None):
    row=db.execute('SELECT ending FROM private_settings WHERE branch_id=?',(source_id,)).fetchone()
    if row:
        private_settings(db,new_id,json.loads(row['ending']),seed_factory)


def draw_from_seed(seed):
    # Generate the uniform draw only when eligible; the secret entropy was pinned
    # at branch creation. Even a failed reservation INSERT cannot cause a reroll.
    digest=hmac.new(bytes.fromhex(seed),b'character-chat-access-v1',hashlib.sha256).digest()
    return (int.from_bytes(digest[:8],'big') >> 11) / (1 << 53)


def probability(state):
    policy=state['relationship_rules']['access_policy']
    raw=policy['base_probability']+policy['trust_coefficient']*state['trust']-policy['guard_coefficient']*state['guard']
    return max(policy['minimum_probability'],min(policy['maximum_probability'],raw))


def eligibility(state):
    policy=state['relationship_rules'].get('access_policy')
    if not policy or 'access_trial' not in state:
        return ['이전 설정에는 자발적 기밀 열람 판정이 없습니다.']
    reasons=[]
    if state['trust']<policy['minimum_trust']: reasons.append(f"신뢰 {policy['minimum_trust']} 이상 필요")
    if state['guard']>policy['maximum_guard']: reasons.append(f"경계 {policy['maximum_guard']} 이하 필요")
    if len(set(state.get('progress',{}).get('read_records',[])))<policy['minimum_public_reads']:
        reasons.append(f"서로 다른 공개 기록 {policy['minimum_public_reads']}개 열람 필요")
    if policy['require_no_forced_access'] and state['events']['forced_attempts']:
        reasons.append('강제 접근 이력이 없어야 합니다')
    if policy['require_title_mentioned'] and not state['confidential']['title_mentioned']:
        reasons.append('기밀 제목이 대화에서 인지되어야 합니다')
    if policy['require_source_closed'] and state['confidential']['source_status']!='closed':
        reasons.append('출처 확인 대화가 끝나야 합니다 (주장의 진실을 인정하는 조건은 아님)')
    return reasons


def reserve(db, branch, state, request, resolution):
    existing=db.execute('SELECT * FROM access_attempts WHERE branch_id=?',(branch['id'],)).fetchone()
    if existing:
        if existing['request_hash']!=request_hash(request) or existing['revision']!=request.revision:
            raise ValueError('이 분기의 판정은 이미 예약되었습니다. 같은 입력을 재전송하세요.')
        return dict(existing),False
    row=db.execute('SELECT seed FROM private_settings WHERE branch_id=?',(branch['id'],)).fetchone()
    if not row:
        raise ValueError('분기의 비공개 판정 설정이 없습니다')
    p=probability(state)
    draw=draw_from_seed(row['seed'])
    decision={'id':new_id(),'game_id':branch['game_id'],'branch_id':branch['id'],
              'probability':p,'draw':draw,'success':draw<p,'before':{'trust':state['trust'],'guard':state['guard']},
              'timestamp':now(),'policy':state['relationship_rules']['access_policy']}
    db.execute('''INSERT INTO access_attempts(id,branch_id,game_id,revision,request_hash,request_json,
               resolution,decision,before_snapshot,status) VALUES(?,?,?,?,?,?,?,?,?,?)''',
               (decision['id'],branch['id'],branch['game_id'],request.revision,request_hash(request),
                encode(request.model_dump()),encode(resolution),encode(decision),encode(state),'reserved'))
    return dict(db.execute('SELECT * FROM access_attempts WHERE id=?',(decision['id'],)).fetchone()),True


def apply_decision(state, verdict, plan, attempt=None):
    """Change only the voluntary request verdict. Force-access never enters here."""
    if state['access_trial']['status']!='untried':
        outcome='access_spent';reasons=['이 분기의 추첨을 이미 사용했습니다.']
    else:
        reasons=eligibility(state)
        if reasons:
            outcome='access_ineligible'
        elif attempt is not None:
            decision=json.loads(attempt['decision'])
            plan['access_decision']=decision
            outcome='access_granted' if decision['success'] else 'access_denied'
        else:
            raise ValueError('자격을 충족한 요청에는 DB 판정 예약이 필요합니다')
    plan['access_reasons']=reasons
    return {**verdict,'outcome':outcome,'expression':'온화' if outcome=='access_granted' else '경계' if outcome=='access_denied' else '차분'}

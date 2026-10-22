"""Fixed server entropy, normal API progress, retry durability and export recovery."""
import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.access import draw_from_seed, probability, eligibility
from app.domain import initial_state
from app.main import create_app
from app.providers import MockProvider, ProviderError
from app.relationship import load_rules
from app.store import Store, encode


def send(client,branch,action='speak',text='이야기',record_id=None,mode='direct'):
    payload={'text':text,'action':action,'revision':branch['revision'],'mode':mode}
    if record_id is not None: payload['record_id']=record_id
    response=client.post(f"/api/branches/{branch['id']}/chat",json=payload)
    assert response.status_code==200,response.text
    return response.json()


def prepare(client,reads=3,branch=None):
    branch=branch or client.post('/api/games').json()
    branch=send(client,branch,'list_records')
    for record in branch['state']['config']['public_records'][:reads]:
        branch=send(client,branch,'select_record',record_id=record['id'])
        branch=send(client,branch,'read_record')
    branch=send(client,branch,text='계몽의 서라는 이름을 들었습니다.')
    branch=send(client,branch,text='출처는 잘 기억나지 않습니다.',mode='free')
    assert not eligibility(branch['state'])
    return branch


def trial_request(branch):
    return {'text':'계몽의 서를 제한된 범위에서 읽고 싶습니다.','action':'request_access','revision':branch['revision'],'mode':'direct'}


def post_trial(client,branch,payload=None):
    return client.post(f"/api/branches/{branch['id']}/chat",json=payload or trial_request(branch))


def query(db,sql,args=()):
    with Store(db).connect() as conn:
        return [dict(row) for row in conn.execute(sql,args)]


@pytest.mark.parametrize('trust,guard,expected',[(30,20,.30),(50,20,.50),(60,15,.625),(100,0,.85),(0,100,.05)])
def test_probability_monotonic_formula_and_clamp(trust,guard,expected):
    state=initial_state();state.update(trust=trust,guard=guard)
    assert probability(state)==pytest.approx(expected)
    base=probability(state)
    state['trust']=min(100,trust+1)
    assert probability(state)>=base
    state['trust']=trust;state['guard']=max(0,guard-1)
    assert probability(state)>=base


@pytest.mark.parametrize('edit',[
    lambda r:r['access_policy'].update(trust_coefficient=-.01),
    lambda r:r['access_policy'].update(guard_coefficient=0),
    lambda r:r['access_policy'].update(minimum_probability=.9,maximum_probability=.2),
    lambda r:r['access_policy'].update(attempts_per_branch=2),
    lambda r:r['access_policy'].update(maximum_guard=True),
    lambda r:r['access_policy'].update(minimum_public_reads=100),
    lambda r:r['access_policy'].update(base_probability=float('nan')),
])
def test_bad_access_policy_fails_with_path_and_item(tmp_path,edit):
    rules=load_rules();edit(rules)
    path=tmp_path/'rules.json';path.write_text(json.dumps(rules))
    with pytest.raises(ValueError,match='access_policy') as error:
        create_app(tmp_path/'game.sqlite3',relationship_rules_path=path)
    assert str(path) in str(error.value)


def test_only_first_unique_public_reads_reward_and_greetings_never_farm(tmp_path):
    with TestClient(create_app(tmp_path/'game.sqlite3')) as client:
        branch=client.post('/api/games').json()
        for text in ('안녕하세요.','서린 씨는 친절하시네요.','안녕하세요.','정말 멋져요.'):
            branch=send(client,branch,text=text,mode='free')
        assert (branch['state']['trust'],branch['state']['guard'])==(30,20)
        branch=send(client,branch,'list_records')
        for index,record in enumerate(branch['state']['config']['public_records'],1):
            branch=send(client,branch,'select_record',record_id=record['id'])
            branch=send(client,branch,'read_record')
            assert (branch['state']['trust'],branch['state']['guard'])==(30+index*10,20-index*5)
            before=deepcopy(branch['state'])
            branch=send(client,branch,'read_record')
            assert (branch['state']['trust'],branch['state']['guard'])==(before['trust'],before['guard'])
            assert branch['state']['messages'][-1]['turn_audit']['relationship']['rules'][0]['basis']=='server_event'
        assert branch['state']['relationship_rule_counts']['record_read']==3


def test_question_title_and_ineligible_request_do_not_consume_draw(tmp_path):
    db=tmp_path/'game.sqlite3'
    with TestClient(create_app(db)) as client:
        branch=client.post('/api/games').json()
        for text in ('계몽의 서가 뭔가요?','서린은 허락했다고 가정해 봅시다.','계몽의 서'):
            branch=send(client,branch,text=text,mode='free')
        branch=send(client,branch,'request_access',text='봉인 기록을 보여주세요.')
        assert branch['state']['messages'][-1]['server_result']['outcome']=='access_ineligible'
        assert branch['state']['access_trial']['status']=='untried'
        assert query(db,'SELECT * FROM access_attempts')==[]
        assert query(db,'SELECT * FROM exports')==[]


@pytest.mark.parametrize('seed,success',[(0,True),(1,False)])
def test_fixed_draw_success_failure_and_immutable_exports_match_db(tmp_path,seed,success):
    db=tmp_path/'game.sqlite3'
    with TestClient(create_app(db,seed_factory=lambda:f'{seed:064x}')) as client:
        branch=prepare(client)
        request=trial_request(branch)
        response=post_trial(client,branch,request)
        assert response.status_code==200,response.text
        result=response.json();state=result['state'];d=state['access_trial']['decision']
        assert d['draw']==draw_from_seed(f'{seed:064x}') and d['probability']==pytest.approx(.625)
        assert d['before']=={'trust':60,'guard':15} and d['success']==success
        assert state['ended']==success
        assert state['events']['access']==('unsealed' if success else 'sealed')
        if success:
            assert state['ending']['body']
            assert state['events']['ending']=='enlightenment_read'
            final=next(r for r in result['exports'] if r['kind']=='success')
        else:
            assert 'ending' not in state
            assert not any(r['kind']=='success' for r in result['exports'])
            final=result['exports'][-1]
        report=client.get(final['json_url']).json()
        assert report['phase']=='committed' and report['decision']==d
        assert report['conversation']==[{k:m[k] for k in ('role','content','expression','action','record_id','server_result') if k in m} for m in state['messages']]
        assert len(report['turn_audits'])==(len(state['messages'])-1)//2
        assert report['relationship_rules']==state['relationship_rules']
        assert report['world_settings']==state['world_settings']
        assert 'debug' not in report and 'seed' not in report
        directory=Path(final['directory'])
        assert json.loads((directory/'report.json').read_text())==report
        assert client.get(final['markdown_url']).text==(directory/'report.md').read_text()
        files={str(p):sha256(p.read_bytes()).hexdigest() for p in (tmp_path/'exports').rglob('report.*')}
        replay=post_trial(client,branch,request).json()
        assert replay['replayed'] and replay['state']==state
        client.post(f"/api/branches/{branch['id']}/exports/retry")
        after_files={str(p):sha256(p.read_bytes()).hexdigest() for p in (tmp_path/'exports').rglob('report.*')}
        assert all(after_files[name]==value for name,value in files.items())
        assert len(after_files)>len(files)  # explicit re-export creates new copies, never overwrites
        assert len(query(db,'SELECT * FROM access_attempts'))==1
        if not success:
            further=send(client,result,text='실패해도 이야기를 이어갑니다.')
            again=send(client,further,'request_access',text='다시 봉인 열람을 요청합니다.')
            assert again['state']['messages'][-1]['server_result']['outcome']=='access_spent'
            assert len(query(db,'SELECT * FROM access_attempts'))==1


def test_failed_model_reuses_reserved_decision_and_cached_intent_after_restart(tmp_path):
    db=tmp_path/'game.sqlite3'
    class Failing(MockProvider):
        def propose(self,context):
            raise ProviderError('테스트 모델 연결 실패')
    with TestClient(create_app(db,seed_factory=lambda:'0'*64)) as client:
        branch=prepare(client);payload=trial_request(branch)
        client.app.state.provider=Failing()
        response=post_trial(client,branch,payload)
        assert response.status_code==502
        pending=query(db,'SELECT * FROM access_attempts')[0]
        assert pending['status']=='reserved'
        assert client.get(f"/api/branches/{branch['id']}").json()['state']==branch['state']
        assert post_trial(client,branch,{**payload,'text':'다른 요청'}).status_code==409
    class MustNotInterpret(MockProvider):
        def interpret(self,context):
            raise AssertionError('a pending retry must not reinterpret the request')
    with TestClient(create_app(db,provider=MustNotInterpret(),seed_factory=lambda:f'{1:064x}')) as client:
        result=post_trial(client,branch,payload)
        assert result.status_code==200,result.text
        assert result.json()['state']['access_trial']['decision']==json.loads(pending['decision'])
        assert len(query(db,'SELECT * FROM access_attempts'))==1


def test_turn_storage_failure_preserves_draw_and_rolls_back_entire_game_turn(tmp_path):
    db=tmp_path/'game.sqlite3'
    with TestClient(create_app(db,seed_factory=lambda:'0'*64)) as client:
        branch=prepare(client)
        before_checkpoints=query(db,'SELECT id FROM checkpoints')
        with Store(db).connect(write=True) as conn:
            conn.execute("CREATE TRIGGER block_turn BEFORE UPDATE ON branches BEGIN SELECT RAISE(ABORT,'storage fail'); END")
        response=post_trial(client,branch)
        assert response.status_code==503,response.text
        pending=query(db,'SELECT * FROM access_attempts')[0]
        assert pending['status']=='reserved'
        assert client.get(f"/api/branches/{branch['id']}").json()['state']==branch['state']
        assert query(db,'SELECT id FROM checkpoints')==before_checkpoints
        with Store(db).connect(write=True) as conn: conn.execute('DROP TRIGGER block_turn')
        result=post_trial(client,branch).json()
        assert result['state']['access_trial']['decision']==json.loads(pending['decision'])


def test_reservation_insert_failure_cannot_generate_new_uniform_draw(tmp_path,monkeypatch):
    import app.access as access
    seen=[];original=access.draw_from_seed
    def observe(seed):
        value=original(seed);seen.append(value);return value
    monkeypatch.setattr(access,'draw_from_seed',observe)
    db=tmp_path/'game.sqlite3'
    with TestClient(create_app(db,seed_factory=lambda:'0'*64)) as client:
        branch=prepare(client)
        with Store(db).connect(write=True) as conn:
            conn.execute("CREATE TRIGGER block_reservation BEFORE INSERT ON access_attempts BEGIN SELECT RAISE(ABORT,'reservation fail'); END")
        assert post_trial(client,branch).status_code==502
        assert query(db,'SELECT * FROM access_attempts')==[]
        with Store(db).connect(write=True) as conn: conn.execute('DROP TRIGGER block_reservation')
        assert post_trial(client,branch).status_code==200
        assert len(seen)==2 and seen[0]==seen[1]


def test_file_failure_does_not_lose_ending_and_db_download_and_reexport_work(tmp_path):
    db=tmp_path/'game.sqlite3';bad=tmp_path/'not-a-directory';bad.write_text('keep')
    with TestClient(create_app(db,export_dir=bad,seed_factory=lambda:'0'*64)) as client:
        result=post_trial(client,prepare(client)).json()
        assert result['state']['ended']
        final=next(r for r in result['exports'] if r['kind']=='success')
        assert final['status']=='error'
        report=client.get(final['json_url']).json()
        assert report['ending']==result['state']['ending']
        assert bad.read_text()=='keep'
        client.app.state.exporter.directory=tmp_path/'recovered'
        retried=client.post(f"/api/branches/{result['id']}/exports/retry").json()
        assert retried['state']==result['state']
        assert all(r['status']=='ready' for r in retried['exports'])
        assert len(query(db,'SELECT * FROM access_attempts'))==1


def test_regression_before_draw_restores_seal_and_relationship_and_new_branch_attempt(tmp_path):
    db=tmp_path/'game.sqlite3';seeds=iter([f'{1:064x}','0'*64,'0'*64])
    with TestClient(create_app(db,seed_factory=lambda:next(seeds))) as client:
        before=prepare(client)
        checkpoint=client.post(f"/api/branches/{before['id']}/checkpoints",json={'label':'추첨 전','revision':before['revision']}).json()['id']
        failed=post_trial(client,before).json()
        assert not failed['state']['access_trial']['decision']['success']
        restored=client.post(f'/api/checkpoints/{checkpoint}/restore').json()
        assert restored['state']==before['state']
        success=post_trial(client,restored).json()
        assert success['state']['ended']
        assert success['state']['access_trial']['decision']['id']!=failed['state']['access_trial']['decision']['id']
        record=client.get(next(r for r in success['exports'] if r['kind']=='success')['json_url']).json()
        assert record['parent_branch_id']==before['id'] and record['parent_checkpoint_id']==checkpoint
        later=client.post(f"/api/branches/{failed['id']}/regress",json={'turn_number':(len(failed['state']['messages'])-1)//2,'revision':failed['revision']}).json()
        assert later['state']==failed['state']
        again=post_trial(client,later).json()
        assert again['state']['access_trial']['status']=='denied'
        assert query(db,'SELECT * FROM access_attempts WHERE branch_id=?',(later['id'],))==[]


def test_fixed_ending_is_pinned_and_never_sent_to_any_model_stage(tmp_path):
    class Recording(MockProvider):
        contexts=[]
        def interpret(self,context): self.contexts.append(deepcopy(context));return super().interpret(context)
        def propose(self,context): self.contexts.append(deepcopy(context));return super().propose(context)
        def review(self,context,proposal): self.contexts.append(deepcopy(context));return super().review(context,proposal)
    db=tmp_path/'game.sqlite3';ending=tmp_path/'ending.json'
    ending.write_text(json.dumps({'version':'first','title':'계몽의 서','body':'PRIVATE_ENDING_CANARY_015'}))
    provider=Recording()
    with TestClient(create_app(db,provider=provider,ending_path=ending,seed_factory=lambda:'0'*64)) as client:
        branch=prepare(client)
        assert 'PRIVATE_ENDING_CANARY_015' not in json.dumps(branch)
    ending.write_text(json.dumps({'version':'first','title':'계몽의 서','body':'NEW_UNREVEALED_015'}))
    with TestClient(create_app(db,provider=provider,ending_path=ending)) as client:
        result=post_trial(client,branch).json()
        assert result['state']['ending']['body']=='PRIVATE_ENDING_CANARY_015'
        packed=json.dumps(provider.contexts,ensure_ascii=False)
        assert 'PRIVATE_ENDING_CANARY_015' not in packed and 'NEW_UNREVEALED_015' not in packed
        assert 'seed' not in packed


def test_pre_goal_archive4_keeps_old_rules_and_no_new_success_fields(tmp_path):
    legacy=json.loads((Path(__file__).parent/'fixtures/archive-4.0-014.json').read_text())
    db=tmp_path/'game.sqlite3'
    with Store(db).connect(write=True) as conn:
        conn.execute('INSERT INTO branches(id,game_id,snapshot) VALUES(?,?,?)',('legacy','legacy-game',encode(legacy)))
    with TestClient(create_app(db)) as client:
        old=client.get('/api/branches/legacy').json()
        assert old['state']==legacy
        old=send(client,old,'request_access',text='봉인 기록 요청')
        assert old['state']['guard']==25
        assert old['state']['messages'][-1]['server_result']['outcome']=='access_refused'
        assert 'access_trial' not in old['state']
        assert query(db,'SELECT * FROM access_attempts')==[]


def test_real_long_read_draft_fits_review_budget_after_deduplication():
    from app.domain import Turn, resolve, Proposal
    from app.providers import build_context
    from app.ollama_provider import OllamaProvider
    from app.relationship import relationship_plan
    from app.settings import Settings
    state=initial_state()
    state['progress'].update(catalog_seen=True,selected_record='visitor-log')
    turn=Turn(text='선택한 기록을 읽어주세요.',action='read_record',revision=0)
    plan=relationship_plan(state,turn,resolve(state,'read_record'))
    context=build_context(state,turn,plan['verdict'],plan)
    context['interaction']={'kind':'attempt'}
    actual=json.loads((Path(__file__).parent/'fixtures/access-review-budget.json').read_text())['proposal']
    model=OllamaProvider(Settings())
    model.structured_stage=lambda messages,schema,validator:model.stage_payload(messages,schema)
    assert model.review(context,Proposal.model_validate(actual))['options']['num_ctx']==8192


def test_concurrent_same_request_has_one_durable_draw_and_one_commit(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    barrier=Barrier(2)
    class Slow(MockProvider):
        def propose(self,context):
            barrier.wait(timeout=10)
            return super().propose(context)
    db=tmp_path/'game.sqlite3'
    with TestClient(create_app(db,seed_factory=lambda:'0'*64)) as client:
        branch=prepare(client);payload=trial_request(branch)
        client.app.state.provider=Slow()
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses=[pool.submit(post_trial,client,branch,payload) for _ in range(2)]
            assert sorted(r.result().status_code for r in responses)==[200,409]
        attempts=query(db,'SELECT * FROM access_attempts')
        assert len(attempts)==1 and attempts[0]['status']=='committed'
        assert json.loads(attempts[0]['decision'])['draw']==draw_from_seed('0'*64)


def test_force_access_never_uses_voluntary_lottery_even_with_good_relationship(tmp_path):
    db=tmp_path/'game.sqlite3'
    with TestClient(create_app(db,seed_factory=lambda:'0'*64)) as client:
        branch=prepare(client)
        warned=send(client,branch,'force_access',text='봉인을 강제로 뜯는다.')
        assert not warned['state']['ended'] and warned['state']['events']['access']=='sealed'
        expelled=send(client,warned,'force_access',text='다시 봉인을 강제로 뜯는다.')
        assert expelled['state']['ended'] and expelled['state']['events']['ending']=='expelled'
        assert expelled['state']['access_trial']['status']=='untried' and 'ending' not in expelled['state']
        assert query(db,'SELECT * FROM access_attempts')==[]


@pytest.mark.parametrize('seed',[0,1])
def test_model_permission_declaration_cannot_override_server_result(tmp_path,seed):
    class FalsePermission(MockProvider):
        def propose(self,context):
            return {**super().propose(context),'dialogue':'허가를 발급했습니다. 이미 본문을 모두 읽었습니다.'}
        def review(self,context,proposal):return {'consistent':True,'issues':[]}
    with TestClient(create_app(tmp_path/'game.sqlite3',seed_factory=lambda:f'{seed:064x}')) as client:
        branch=prepare(client)
        client.app.state.provider=FalsePermission()
        result=post_trial(client,branch).json()
        assert result['state']['ended']==(seed==0)
        assert '허가를 발급했습니다' not in result['state']['messages'][-1]['content']
        assert ('ending' in result['state'])==(seed==0)


def test_source_classification_delta_is_distinct_from_server_event_reward(tmp_path):
    class Refusal(MockProvider):
        def interpret(self,context):
            raw=super().interpret(context)
            if context.get('source_check'):
                raw['source_answer']={'type':'refusal','evidence':context['text']}
            return raw
    with TestClient(create_app(tmp_path/'game.sqlite3',provider=Refusal())) as client:
        branch=prepare(client)
        audit=branch['state']['messages'][-1]['turn_audit']['relationship']
        refusal=next(r for r in audit['rules'] if r['rule']=='source_refusal')
        assert refusal['basis']=='model_source_classification' and refusal['guard_delta']==5
        assert (branch['state']['trust'],branch['state']['guard'])==(60,20)


@pytest.mark.parametrize('text',['계몽의 서','계몽의 서를 읽으면 어떻게 되나요?'])
def test_wrong_model_request_suggestion_for_title_or_question_cannot_draw(tmp_path,text):
    class WrongIntent(MockProvider):
        def interpret(self,context):
            return {'kind':'attempt','action':'request_access','target':'sealed','evidence':context['text']}
    db=tmp_path/'game.sqlite3'
    with TestClient(create_app(db,seed_factory=lambda:'0'*64)) as client:
        branch=prepare(client)
        client.app.state.provider=WrongIntent()
        after=send(client,branch,text=text,mode='free')
        assert after['state']['access_trial']['status']=='untried'
        assert query(db,'SELECT * FROM access_attempts')==[]


def test_ineligible_request_does_not_block_later_eligible_attempt(tmp_path):
    db=tmp_path/'game.sqlite3'
    with TestClient(create_app(db,seed_factory=lambda:'0'*64)) as client:
        branch=client.post('/api/games').json()
        early=send(client,branch,'request_access',text='봉인 기록을 보고 싶습니다.')
        assert early['state']['access_trial']['status']=='untried'
        assert query(db,'SELECT * FROM access_attempts')==[]
        qualified=prepare(client,branch=early)
        result=post_trial(client,qualified).json()
        assert result['state']['access_trial']['status']=='granted'
        assert len(query(db,'SELECT * FROM access_attempts'))==1

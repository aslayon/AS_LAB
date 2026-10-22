import json
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain import initial_state, resolve, Turn
from app.providers import build_context
from app.dialogue_review import grounded_reply
from app.main import create_app
from app.relationship import load_rules
from app.store import Store, encode


@pytest.mark.parametrize('change',[
    lambda r:r.update(version=''),
    lambda r:r['initial'].update(trust=101),
    lambda r:r['bounds'].update(minimum=100,maximum=0),
    lambda r:r['thresholds'].update(source_rechecks=0),
    lambda r:r['thresholds'].update(forced_access_end_attempts=1),
    lambda r:r['rules']['forced_access'].update(guard_delta='25'),
    lambda r:r['rules']['forced_access'].update(guard_delta=True),
    lambda r:r['rules']['forced_access'].update(guard_delta=101),
    lambda r:r['rules']['secret_first_mention'].update(max_applications_per_branch=2),
    lambda r:r['rules'].pop('conversation'),
    lambda r:r.update(unknown=1),
])
def test_bad_tuning_fails_at_startup(tmp_path,change):
    rules=load_rules();change(rules)
    path=tmp_path/'rules.json';path.write_text(json.dumps(rules))
    with pytest.raises(ValueError,match='관계 규칙 설정 오류'):
        create_app(tmp_path/'db.sqlite3',relationship_rules_path=path)


@pytest.mark.parametrize('contents',['{','{"version":"a","version":"b"}'])
def test_bad_or_duplicate_json_has_clear_error(tmp_path,contents):
    path=tmp_path/'rules.json';path.write_text(contents)
    with pytest.raises(ValueError,match='관계 규칙 설정 오류'):
        create_app(tmp_path/'db.sqlite3',relationship_rules_path=path)


def send(client,b,text,action='speak'):
    response=client.post(f"/api/branches/{b['id']}/chat",json={'text':text,'action':action,'revision':b['revision']})
    assert response.status_code==200,response.text
    return response.json()


def test_restart_new_game_and_restore_pin_actual_tuning(tmp_path):
    path=tmp_path/'rules.json';old=load_rules();path.write_text(json.dumps(old))
    db=tmp_path/'test.sqlite3'
    with TestClient(create_app(db,relationship_rules_path=path)) as client:
        branch=client.post('/api/games').json()
        cp=client.post(f"/api/branches/{branch['id']}/checkpoints",json={'label':'초기','revision':0}).json()
        new=deepcopy(old);new['version']='relationship-test-2';new['initial']['guard']=7
        new['rules']['secret_first_mention']['guard_delta']=3
        new['rules']['sealed_request'].update(guard_delta=2,max_applications_per_branch=1)
        new['thresholds']['forced_access_end_attempts']=3
        path.write_text(json.dumps(new))
        assert client.post('/api/games').json()['state']['relationship_rules']==old
    with TestClient(create_app(db,relationship_rules_path=path)) as client:
        fresh=client.post('/api/games').json()
        assert fresh['state']['relationship_rules']==new
        assert fresh['state']['guard']==7
        fresh=send(client,fresh,'계몽의 서')
        assert fresh['state']['guard']==10
        fresh=send(client,fresh,'봉인 요청','request_access')
        assert fresh['state']['guard']==12
        fresh=send(client,fresh,'봉인 요청','request_access')
        assert fresh['state']['guard']==12  # max applications from saved tuning
        original=client.get(f"/api/branches/{branch['id']}").json()
        original=send(client,original,'계몽의서')
        assert original['state']['guard']==30
        restored=client.post(f"/api/checkpoints/{cp['id']}/restore").json()
        assert restored['state']==branch['state']
        assert restored['state']['relationship_rules']==old
        # Threshold changes are real, and still use the saved branch values.
        fresh=send(client,fresh,'강제 접근','force_access')
        fresh=send(client,fresh,'강제 접근','force_access')
        assert not fresh['state']['ended']
        context=build_context(fresh['state'],Turn(text='봉인을 뜯으면요?',revision=0),resolve(fresh['state'],'speak'))
        context['interaction']={'focus':'sealed'}
        assert '3회' in grounded_reply(context)
        assert '3회' in fresh['state']['messages'][-1]['server_result']['message']
        fresh=send(client,fresh,'강제 접근','force_access')
        assert fresh['state']['ended']


@pytest.mark.parametrize('fixture',['archive-2.0-snapshot.json','archive-3.0-snapshot.json'])
def test_old_snapshot_has_implicit_historical_numbers_and_no_migration(tmp_path,fixture):
    legacy=json.loads((Path(__file__).parent/'fixtures'/fixture).read_text())
    db=tmp_path/'test.sqlite3';store=Store(db)
    with store.connect(write=True) as conn:
        conn.execute('INSERT INTO branches(id,game_id,snapshot) VALUES(?,?,?)',('old','old-game',encode(legacy)))
    tuning=load_rules();tuning['rules']['forced_access']['guard_delta']=1
    path=tmp_path/'rules.json';path.write_text(json.dumps(tuning))
    with TestClient(create_app(db,relationship_rules_path=path)) as client:
        old=client.get('/api/branches/old').json()
        assert old['state']==legacy
        cp=client.post('/api/branches/old/checkpoints',json={'label':'옛 상태','revision':0}).json()
        old=send(client,old,'계몽의 서')
        assert old['state']['guard']==legacy['guard']
        assert 'confidential' not in old['state'] and 'relationship_rules' not in old['state']
        old=send(client,old,'강제 접근','force_access')
        assert old['state']['guard']==legacy['guard']+25
        assert old['state']['trust']==legacy['trust']-15
        restored=client.post(f"/api/checkpoints/{cp['id']}/restore").json()
        assert restored['state']==legacy

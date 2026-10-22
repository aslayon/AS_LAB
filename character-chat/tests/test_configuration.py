"""Golden pre-refactor inputs, startup validation, snapshot isolation and disclosure boundaries."""
import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain import initial_state, Turn, resolve, Proposal, apply_turn
from app.relationship import load_rules, relationship_plan
from app.intent import intent_context
from app.main import create_app
from app.providers import MockProvider, build_context
from app.ollama_provider import OllamaProvider
from app.settings import Settings
from app.world import load_world


def capture(world=None, rules=None):
    provider = OllamaProvider(Settings())
    provider.structured_stage = lambda messages, schema, validator: {'messages': messages, 'schema': schema}
    initial = initial_state(relationship_rules=rules,world=world)
    cases = []
    for sequence in [
        [('speak', '안녕하세요.', None), ('list_records','목록을 보여주세요.',None),
         ('select_record','방문 기록을 선택합니다.','visitor-log'), ('read_record','읽어주세요.',None),
         ('speak','방금 읽은 내용은요?',None)],
        [('request_access','봉인 기록을 보여주세요.',None),('force_access','봉인을 강제로 뜯는다.',None),
         ('force_access','다시 봉인을 뜯는다.',None)],
        [('speak','계몽의 서',None), ('speak','출처를 말하지 않겠습니다.',None)],
        [('leave','떠납니다.',None)],
    ]:
        state = deepcopy(initial)
        for action, text, record_id in sequence:
            turn = Turn(text=text, action=action, record_id=record_id, revision=0)
            plan = relationship_plan(state, turn, resolve(state,action,record_id))
            context = build_context(state, turn, plan['verdict'], plan)
            context['interaction'] = {'kind': 'conversation' if action == 'speak' else 'direct', 'focus': None}
            proposal = Proposal.model_validate(MockProvider().propose(context))
            ic = intent_context(state,text)
            cases.append({'verdict': plan['verdict'], 'context': deepcopy(context),
                          'intent': provider.interpret(ic), 'draft': provider.payload(context),
                          'review': provider.review(context, proposal)})
            state = apply_turn(state,turn,proposal,plan['verdict'],plan)
    return {'initial_state': initial, 'cases': cases}

def test_pre_refactor_verdicts_and_all_model_stage_inputs_unchanged():
    expected = json.loads((Path(__file__).parent / 'fixtures/world-before-refactor.json').read_text())
    previous_world = deepcopy(expected['initial_state']['config'])
    previous_world.pop('confidential_policy_version')
    previous_world['first_dialogue'] = expected['initial_state']['messages'][0]['content']
    actual = capture(previous_world, expected['initial_state']['relationship_rules'])
    # Only the raw world snapshot and editable greeting field are added.
    assert actual['initial_state'].pop('world_settings') == previous_world
    assert actual['initial_state']['config'].pop('first_dialogue') == expected['initial_state']['messages'][0]['content']
    assert actual['initial_state'] == expected['initial_state']
    for case in actual['cases']:
        for key in ('context', 'intent', 'draft', 'review'):
            case[key] = sha256(json.dumps(case[key],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    assert actual['cases'] == expected['cases']


@pytest.mark.parametrize('edit,field', [
    (lambda w: w.pop('character'), 'character'),
    (lambda w: w.update(environment='   '), 'environment'),
    (lambda w: w.update(first_dialogue=12), 'first_dialogue'),
    (lambda w: w.update(known_facts=['']), 'known_facts.0'),
    (lambda w: w.update(core=['성격만']), 'core'),
    (lambda w: w.update(public_records=[]), 'public_records'),
    (lambda w: w['public_records'][0].update(content=False), 'public_records.0.content'),
    (lambda w: w['public_records'][1].update(id=w['public_records'][0]['id']), 'public_records.1.id'),
    (lambda w: w['public_records'][1].update(title=w['public_records'][0]['title']), 'public_records.1.title'),
    (lambda w: w['public_records'][0].update(id='sealed'), 'public_records.0.id'),
    (lambda w: w.update(player_only='PRIVATE_CANARY'), 'player_only'),
    (lambda w: w.update(confidential_policy_version='secret'), 'confidential_policy_version'),
])
def test_world_invalid_value_reports_path_and_item_before_database_creation(tmp_path, edit, field):
    world = load_world(); edit(world)
    path = tmp_path / 'world.json'; path.write_text(json.dumps(world), encoding='utf-8')
    db = tmp_path / 'not-created.sqlite3'
    with pytest.raises(ValueError) as error:
        create_app(db, world_path=path)
    assert str(path) in str(error.value) and field in str(error.value)
    assert not db.exists()


@pytest.mark.parametrize('filename,raw,field', [
    ('world.json', '{', '$'),
    ('world.json', '{"version":"a","version":"b"}', 'version'),
    ('world.json', '[]', '$'),
    ('rules.json', '{', '$'),
    ('rules.json', '{"rules":{},"rules":{}}', 'rules'),
])
def test_invalid_json_reports_file_and_item(tmp_path, filename, raw, field):
    path = tmp_path / filename; path.write_text(raw, encoding='utf-8')
    kwargs = {'world_path' if filename == 'world.json' else 'relationship_rules_path': path}
    with pytest.raises(ValueError) as error:
        create_app(tmp_path / 'test.sqlite3', **kwargs)
    assert str(path) in str(error.value) and field in str(error.value)


def test_configuration_startup_snapshot_same_version_edits_and_regression(tmp_path):
    world, rules = load_world(), load_rules()
    wp, rp, db = tmp_path / 'world.json', tmp_path / 'rules.json', tmp_path / 'game.sqlite3'
    def write():
        wp.write_text(json.dumps(world,ensure_ascii=False),encoding='utf-8')
        rp.write_text(json.dumps(rules),encoding='utf-8')
    def send(client, branch, text, action='speak', record_id=None):
        payload = {'text':text,'action':action,'revision':branch['revision']}
        if record_id is not None:
            payload['record_id'] = record_id
        response = client.post(f"/api/branches/{branch['id']}/chat",json=payload)
        assert response.status_code == 200,response.text
        return response.json()
    write()
    with TestClient(create_app(db,world_path=wp,relationship_rules_path=rp)) as client:
        original = client.post('/api/games').json()
        first = send(client,original,'첫 발언')
        cp = client.post(f"/api/branches/{first['id']}/checkpoints",json={'label':'old','revision':first['revision']}).json()['id']
        later = send(client,first,'FUTURE_AFTER_CHECKPOINT','force_access')
        # Same version strings, different actual values: restart is required.
        world.update(character='다른 보관인',environment='맑은 아침.',first_dialogue='어서 오세요.')
        world['core'][0]='느긋하고 친절한 보관인이다.'
        world['known_facts']=['문서들을 정리하고 있다.']
        world['public_records'][0].update(id='custom-visitor-log',title='새 방문 기록',content='NEW_RECORD_BODY')
        rules['initial'].update(trust=75,guard=6)
        rules['rules']['sealed_request']['guard_delta']=2
        write()
        unchanged = client.post('/api/games').json()
        assert unchanged['state'] == original['state']
        # Caller mutations cannot change startup settings either.
        unchanged['state']['config']['core'][0]='CLIENT_MUTATION'
        assert client.post('/api/games').json()['state'] == original['state']
    class Recording(MockProvider):
        def __init__(self):
            self.contexts = []
        def propose(self,context):
            self.contexts.append(deepcopy(context))
            return super().propose(context)
    provider=Recording()
    with TestClient(create_app(db,provider=provider,world_path=wp,relationship_rules_path=rp)) as client:
        fresh = client.post('/api/games').json()
        state = fresh['state']
        assert state['config_version'] == original['state']['config_version']
        assert state['relationship_rules']['version'] == original['state']['relationship_rules']['version']
        assert state['world_settings'] == world
        for key in world:
            if key == 'core':
                assert state['config']['core'][:-1] == world['core'][:-1]
            else:
                assert state['config'][key] == world[key]
        assert state['relationship_rules'] == rules
        assert (state['trust'],state['guard']) == (75,6)
        assert state['messages'][0]['content'] == '어서 오세요.'
        fresh = send(client,fresh,'봉인 기록 요청','request_access')
        assert fresh['state']['guard'] == 8
        assert provider.contexts[-1]['instructions']['environment'] == '맑은 아침.'
        assert provider.contexts[-1]['instructions']['core'][0] == world['core'][0]
        fresh = send(client,fresh,'목록','list_records')
        fresh = send(client,fresh,'선택','select_record','custom-visitor-log')
        fresh = send(client,fresh,'열람','read_record')
        assert fresh['state']['messages'][-1]['server_result']['record'] == world['public_records'][0]
        assert intent_context(fresh['state'],'새 방문 기록을 선택합니다.')['selection_targets']['새 방문 기록'] == 'custom-visitor-log'
        assert client.get(f"/api/branches/{later['id']}").json() == later
        restored = client.post(f'/api/checkpoints/{cp}/restore').json()
        assert restored['state'] == first['state']
        regressed = client.post(f"/api/branches/{later['id']}/regress",json={'turn_number':1,'revision':later['revision']}).json()
        assert regressed['state'] == first['state']
        old = send(client,regressed,'봉인 기록 요청','request_access')
        assert old['state']['guard'] == first['state']['guard']+original['state']['relationship_rules']['rules']['sealed_request']['guard_delta']
        context = provider.contexts[-1]
        assert context['instructions']['environment'] == original['state']['config']['environment']
        assert 'NEW_RECORD_BODY' not in json.dumps(context,ensure_ascii=False)
        assert 'FUTURE_AFTER_CHECKPOINT' not in json.dumps(context,ensure_ascii=False)


def test_new_world_loader_does_not_import_secrets_or_expand_model_audience():
    world = load_world()
    packed_world = json.dumps(world,ensure_ascii=False)
    for secret in ('계몽의 서','serin_knows_location','player_only','confidential_policy_version'):
        assert secret not in packed_world
    state = initial_state(world=world)
    state['config'].update(author_notes='AUTHOR_PRIVATE_CANARY',player_only='PLAYER_PRIVATE_CANARY',unknown='UNKNOWN_PRIVATE_CANARY')
    model = OllamaProvider(Settings())
    model.structured_stage=lambda messages,schema,validator: {'messages':messages,'schema':schema}
    turn=Turn(text='안녕하세요.',revision=0)
    context=build_context(state,turn,resolve(state,'speak'))
    context['interaction']={'kind':'conversation','focus':None}
    proposal=Proposal.model_validate(MockProvider().propose(context))
    inputs=[model.interpret(intent_context(state,turn.text)),model.payload(context),model.review(context,proposal)]
    packed=json.dumps(inputs,ensure_ascii=False)
    for secret in ('계몽의 서','AUTHOR_PRIVATE_CANARY','PLAYER_PRIVATE_CANARY','UNKNOWN_PRIVATE_CANARY','serin_knows_location','confidential_policy_version','first_dialogue'):
        assert secret not in packed
    for record in world['public_records']:
        assert record['content'] not in packed


def test_pre_refactor_archive4_snapshot_restores_without_new_world_fields(tmp_path):
    from app.store import Store, encode

    old = json.loads((Path(__file__).parent / 'fixtures/world-before-refactor.json').read_text())['initial_state']
    db = tmp_path / 'old.sqlite3'
    with Store(db).connect(write=True) as conn:
        conn.execute('INSERT INTO branches(id,game_id,snapshot) VALUES(?,?,?)',('old','old-game',encode(old)))
    world = load_world()
    world.update(environment='바뀐 환경',first_dialogue='바뀐 인사')
    path = tmp_path / 'world.json'
    path.write_text(json.dumps(world), encoding='utf-8')
    with TestClient(create_app(db,world_path=path)) as client:
        branch = client.get('/api/branches/old').json()
        assert branch['state'] == old
        checkpoint = client.post('/api/branches/old/checkpoints',json={'label':'old','revision':0}).json()
        response = client.post('/api/branches/old/chat',json={'text':'안녕하세요.','revision':0})
        assert response.status_code == 200
        assert response.json()['state']['config'] == old['config']
        assert 'world_settings' not in response.json()['state']
        restored = client.post(f"/api/checkpoints/{checkpoint['id']}/restore").json()
        assert restored['state'] == old

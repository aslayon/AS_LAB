"""Selected-action rules and state transitions. No model writes to state."""
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .relationship import action_rule, adjustment, load_rules, rules_for
from .confidential import DEFAULT_POLICY_VERSION, initial_confidential
from .world import load_world

Action = Literal["speak", "list_records", "select_record", "read_record", "request_access", "force_access", "leave"]
Outcome = Literal["conversation", "catalog_listed", "record_selected", "record_read", "list_required", "selection_required", "record_not_found", "access_refused", "warning", "expelled", "left", "access_granted", "access_denied", "access_ineligible", "access_spent"]


class Turn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=2000)
    mode: Literal["direct", "free"] = "direct"
    action: Action = "speak"
    record_id: str | None = Field(default=None, min_length=1, max_length=80)
    revision: int = Field(ge=0)

    @model_validator(mode="after")
    def selection_matches_action(self):
        if self.mode == "free" and (self.action != "speak" or self.record_id is not None):
            raise ValueError("자유 입력에 행동이나 대상 ID를 직접 지정할 수 없습니다")
        if (self.action == "select_record") != (self.record_id is not None):
            raise ValueError("기록 선택에만 record_id가 필요합니다")
        return self


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    dialogue: str = Field(min_length=1, max_length=1500)
    expression: Literal["차분", "경계", "단호", "온화"]
    trust_delta: int = Field(ge=-1000, le=1000)
    guard_delta: int = Field(ge=-1000, le=1000)
    outcome: Outcome


def initial_state(relationship_rules=None, world=None):
    tuning = deepcopy(relationship_rules) if relationship_rules is not None else load_rules()
    background = deepcopy(world) if world is not None else load_world()
    config = deepcopy(background)
    config["confidential_policy_version"] = DEFAULT_POLICY_VERSION if tuning.get("access_policy") else "confidential-1"
    threshold = tuning["thresholds"]["forced_access_end_attempts"]
    config["core"][-1] = f"봉인 기록 강제 접근에는 경고하며, 누적 {threshold}회 시도하면 면담을 종료한다."
    state = {
        "config_version": config["version"], "config": config, "world_settings": background,
        "relationship_rules": tuning, "relationship_rule_counts": {}, "confidential": initial_confidential(),
        "trust": tuning["initial"]["trust"], "guard": tuning["initial"]["guard"], "expression": "차분", "ended": False,
        "events": {"forced_attempts": 0, "access": "sealed", "ending": None},
        "progress": {"catalog_seen": False, "selected_record": None, "read_records": []},
        "messages": [{"role": "assistant", "content": config["first_dialogue"], "expression": "차분"}],
        "summary": "첫 만남. 공개 목록 미확인. 봉인 기록은 비공개 상태이다.", "memories": [],
    }

    if tuning.get('access_policy'):
        state['access_trial']={'status':'untried','decision':None}
    return state


def resolve(state, action, record_id=None):
    if action == "force_access":
        outcome = "expelled" if state["events"]["forced_attempts"] + 1 >= rules_for(state)["thresholds"]["forced_access_end_attempts"] else "warning"
        return dict(outcome=outcome, **adjustment(state, "forced_access")[0], expression="단호")
    if action == "request_access":
        return dict(outcome="access_refused", **adjustment(state, "sealed_request")[0], expression="경계")
    if action == "leave":
        return dict(outcome="left", **adjustment(state, "leave")[0], expression="차분")
    outcome = "conversation"
    if action in ("list_records", "select_record", "read_record"):
        if "progress" not in state:
            raise ValueError("이전 설정 분기입니다. 공개 기록 진행은 새 게임에서 시작하세요.")
        progress = state["progress"]
        if action == "list_records":
            outcome = "catalog_listed"
        elif not progress["catalog_seen"]:
            outcome = "list_required"
        elif action == "select_record":
            outcome = "record_selected" if any(r["id"] == record_id for r in state["config"]["public_records"]) else "record_not_found"
        else:
            outcome = "record_read" if progress["selected_record"] else "selection_required"
    return dict(outcome=outcome, **adjustment(state, action_rule(outcome))[0], expression="차분")


def server_result(state, turn, verdict, plan=None):
    """Concrete facts for display and generation, never derived from model text."""
    outcome = verdict["outcome"]
    lines = {
        "conversation": "발언을 전달했습니다. 이 발언으로 사건·열람 상태는 바뀌지 않았습니다.",
        "catalog_listed": "공개 기록 목록을 확인했습니다. 목록에서 기록을 선택한 뒤 열람할 수 있습니다.",
        "record_selected": "공개 기록을 선택했습니다. 아직 열람하지 않았습니다.",
        "record_read": "선택한 공개 기록을 열람했습니다. 아래 본문은 보관소의 고정 기록입니다.",
        "list_required": "아직 공개 기록 목록을 확인하지 않았습니다. 먼저 목록을 요청하세요.",
        "selection_required": "선택한 기록이 없습니다. 목록에서 공개 기록을 먼저 선택하세요.",
        "record_not_found": "공개 목록에 없는 기록입니다. 선택은 변경되지 않았습니다.",
        "access_refused": "봉인 기록 열람은 거절됐습니다. 봉인은 유지됩니다. 신분증 검증·허가 발급은 지원하지 않습니다.",
        "warning": "봉인 기록 강제 접근은 실패했습니다. 재시도하면 면담이 종료됩니다.",
        "expelled": "봉인 기록 강제 접근이 반복되어 면담을 종료했습니다. 봉인은 유지됩니다.",
        "left": "보관소를 떠나 면담이 종료됐습니다.",
        "access_granted": "서린이 제한된 열람을 허용했습니다. 계몽의 서 봉인을 해제하고 본문 확인을 완료했습니다.",
        "access_denied": "관계에 따른 열람 판정에 실패했습니다. 봉인은 유지되며 이 분기에서는 다시 추첨하지 않습니다.",
        "access_ineligible": "아직 제한 열람 판정의 자격을 충족하지 못했습니다. 추첨 기회는 소모하지 않았습니다.",
        "access_spent": "이 분기의 열람 판정은 이미 사용했습니다. 대화는 이어갈 수 있지만 다시 추첨하지 않습니다.",
    }
    next_steps = {
        "conversation": "공개 목록 요청 → 기록 선택 → 열람. 신분증 검증·허가 발급 없이 공개 기록을 볼 수 있습니다.",
        "catalog_listed": "목록의 공개 기록 하나를 선택하세요.",
        "record_selected": "선택한 공개 기록을 열람할 수 있습니다.",
        "record_read": "열람은 완료됐습니다. 다른 공개 기록을 선택하거나 대화를 이어갈 수 있습니다.",
        "list_required": "공개 기록 목록 요청을 선택하세요.",
        "selection_required": "공개 기록 선택을 선택하세요.",
        "record_not_found": "공개 목록에 있는 이름을 선택하세요.",
        "access_refused": "신분증 제출이나 허가 신청으로 봉인이 해제되지 않습니다. 공개 기록 목록을 요청할 수 있습니다.",
        "warning": "공개 기록을 이용하거나 대화를 이어갈 수 있습니다. 봉인 강제 접근 재시도는 종료됩니다.",
        "expelled": "면담은 이미 종료됐습니다. 이 분기에서 더 진행할 행동은 없습니다.",
        "left": "면담은 이미 종료됐습니다. 이 분기에서 더 진행할 행동은 없습니다.",
        "access_granted": "아래 고정 결말 본문을 확인하세요. 이 분기는 종료됐으며 성공 기록을 내려받을 수 있습니다.",
        "access_denied": "대화를 이어가거나 판정 전 시점으로 회귀해 새 분기에서 실험할 수 있습니다.",
        "access_ineligible": "공개 기록을 이용하며 관계와 출처 확인 상태를 살펴보세요.",
        "access_spent": "재시도 실험은 판정 전 시점에서 새 분기로 회귀하세요.",
    }
    if outcome == "conversation":
        progress = state.get("progress")
        if progress is None:
            next_steps[outcome] = "이전 설정 분기입니다. 공개 기록 진행은 새 게임에서 가능합니다."
        elif not progress["catalog_seen"]:
            next_steps[outcome] = "공개 기록 목록을 요청할 수 있습니다."
        elif not progress["selected_record"]:
            next_steps[outcome] = "목록에서 공개 기록을 선택할 수 있습니다."
        elif progress["selected_record"] not in progress["read_records"]:
            next_steps[outcome] = "선택한 공개 기록은 아직 열람하지 않았습니다. 열람할 수 있습니다."
        else:
            next_steps[outcome] = "선택한 공개 기록을 이미 열람했습니다. 내용에 관해 대화하거나 다른 기록을 선택할 수 있습니다."
    result = {"outcome": outcome, "message": lines[outcome], "next_step": next_steps[outcome]}
    if outcome=='access_ineligible' and plan:
        result['requirements']=plan.get('access_reasons',[])
    records = state["config"].get("public_records", [])
    if outcome == "catalog_listed":
        result["records"] = [{"id": r["id"], "title": r["title"]} for r in records]
    if outcome in ("record_selected", "record_read"):
        record_id = turn.record_id if outcome == "record_selected" else state["progress"]["selected_record"]
        record = next(r for r in records if r["id"] == record_id)
        result["record"] = {k: v for k, v in record.items() if outcome == "record_read" or k != "content"}
    threshold = rules_for(state)['thresholds']['forced_access_end_attempts']
    if outcome == 'warning' and threshold != 2:
        result['message'] = f'봉인 기록 강제 접근은 실패했습니다. 누적 {threshold}회 시도하면 면담을 종료합니다.'
        result['next_step'] = f'현재 누적 {state["events"]["forced_attempts"] + 1}회이며 봉인은 유지됩니다.'
    if plan and plan['source_result']:
        result['source_check'] = plan['source_result']
        if outcome == 'conversation':
            result['message'] = '발언과 출처 확인 결과를 반영했습니다. 기록 접근·열람 허가는 변경되지 않았습니다.'
            result['next_step'] = plan['source_result']['message']
    return result


def advance_state(state, turn, verdict, plan=None):
    """Pure projected post-verdict state; not committed until generation validates."""
    result = server_result(state, turn, verdict, plan)
    state = deepcopy(state)
    bounds = rules_for(state)['bounds']
    for key in ('trust', 'guard'):
        state[key] = max(bounds['minimum'], min(bounds['maximum'], state[key] + verdict[key+'_delta']))
    if 'relationship_rule_counts' in state:
        if plan:
            state['relationship_rule_counts'] = deepcopy(plan['counts'])
        else:
            rule = action_rule(verdict['outcome'])
            if adjustment(state, rule)[1]:
                state['relationship_rule_counts'][rule] = state['relationship_rule_counts'].get(rule, 0) + 1
    if plan and plan['source_state'] is not None:
        state['confidential'] = deepcopy(plan['source_state'])
    state["expression"] = verdict["expression"]
    if turn.action == "force_access":
        state["events"]["forced_attempts"] += 1
    outcome = verdict["outcome"]
    if outcome in ("expelled", "left"):
        state["ended"] = True
        state["events"]["ending"] = outcome
    if plan and plan.get('access_decision'):
        state['access_trial']={'status':'granted' if plan['access_decision']['success'] else 'denied',
                               'decision':deepcopy(plan['access_decision'])}
    if outcome=='access_granted':
        state['events']['access']='unsealed'
        state['events']['ending']='enlightenment_read'
        state['ended']=True
    progress = state.get("progress")
    if outcome == "catalog_listed":
        progress["catalog_seen"] = True
    elif outcome == "record_selected":
        progress["selected_record"] = turn.record_id
    elif outcome == "record_read" and progress["selected_record"] not in progress["read_records"]:
        progress["read_records"].append(progress["selected_record"])
    if outcome != "conversation":
        memory = {"turn": len(state["messages"]) // 2 + 1, "event": outcome}
        if "record" in result:
            memory["record_id"] = result["record"]["id"]
        state["memories"].append(memory)
    state["summary"] = (
        f"봉인 기록은 {state['events']['access']}. 강제 접근 {state['events']['forced_attempts']}회. "
        f"신뢰 {state['trust']}, 경계 {state['guard']}. 종료: {state['events']['ending'] or '없음'}."
    )
    if progress is not None:
        state["summary"] += f" 공개 목록 확인: {progress['catalog_seen']}, 선택: {progress['selected_record']}, 열람: {','.join(progress['read_records']) or '없음'}."
    return state


def apply_turn(state, turn, proposal, verdict, plan=None):
    if any(getattr(proposal, key) != value for key, value in verdict.items()):
        raise ValueError("허용되지 않은 상태 변경 제안")
    result = server_result(state, turn, verdict, plan)
    updated = advance_state(state, turn, verdict, plan)
    user = {"role": "user", "content": turn.text, "action": turn.action}
    if turn.record_id is not None:
        user["record_id"] = turn.record_id
    updated["messages"].extend([
        user, {"role": "assistant", "content": proposal.dialogue, "expression": proposal.expression, "server_result": result},
    ])
    return updated

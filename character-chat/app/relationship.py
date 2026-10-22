"""Validated tuning snapshots; semantic transitions stay in server code."""
from copy import deepcopy
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .configuration import load_configuration

RULE_IDS = ('conversation', 'catalog_listed', 'record_selected', 'record_read', 'public_request_rejected',
            'sealed_request', 'forced_access', 'leave', 'secret_first_mention', 'source_refusal', 'source_evasion')
DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'config' / 'relationship_rules.json'


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Adjustment(StrictModel):
    trust_delta: int = Field(ge=-100, le=100)
    guard_delta: int = Field(ge=-100, le=100)
    max_applications_per_branch: int | None = Field(ge=0, le=10000)


class Numbers(StrictModel):
    trust: int = Field(ge=0, le=100)
    guard: int = Field(ge=0, le=100)


class Bounds(StrictModel):
    minimum: int = Field(ge=0, le=100)
    maximum: int = Field(ge=0, le=100)


class Thresholds(StrictModel):
    forced_access_end_attempts: int = Field(ge=2, le=100)
    source_rechecks: int = Field(ge=1, le=3)


class AccessPolicy(StrictModel):
    minimum_trust: int = Field(ge=0,le=100)
    maximum_guard: int = Field(ge=0,le=100)
    minimum_public_reads: int = Field(ge=0,le=100)
    require_no_forced_access: bool
    require_title_mentioned: bool
    require_source_closed: bool
    base_probability: float = Field(ge=-1,le=1,allow_inf_nan=False)
    trust_coefficient: float = Field(gt=0,le=1,allow_inf_nan=False)
    guard_coefficient: float = Field(gt=0,le=1,allow_inf_nan=False)
    minimum_probability: float = Field(ge=0,le=1,allow_inf_nan=False)
    maximum_probability: float = Field(ge=0,le=1,allow_inf_nan=False)
    attempts_per_branch: int = Field(ge=1,le=1)

    @model_validator(mode='after')
    def ordered(self):
        if self.minimum_probability>self.maximum_probability:
            raise ValueError('access_policy.minimum_probability <= maximum_probability 이어야 합니다')
        return self


class RelationshipRules(StrictModel):
    version: str = Field(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9._-]+$')
    initial: Numbers
    bounds: Bounds
    thresholds: Thresholds
    rules: dict[str, Adjustment]
    access_policy: AccessPolicy | None = None

    @model_validator(mode='after')
    def coherent(self):
        if set(self.rules) != set(RULE_IDS):
            raise ValueError('rules에는 다음 규칙이 정확히 필요합니다: ' + ', '.join(RULE_IDS))
        if self.bounds.minimum >= self.bounds.maximum or any(
                not self.bounds.minimum <= n <= self.bounds.maximum for n in (self.initial.trust, self.initial.guard)):
            raise ValueError('bounds의 최소/최대 및 initial 범위를 확인하세요')
        # A semantic event remains once-only even when its numeric adjustment is disabled.
        for key in ('secret_first_mention', 'source_refusal', 'source_evasion'):
            if self.rules[key].max_applications_per_branch not in (0, 1):
                raise ValueError(key + ' 반복 적용 한도는 0(수치 비활성) 또는 1입니다')
        return self


def validate_rules(value):
    return RelationshipRules.model_validate(value).model_dump(exclude_unset=True)


def load_rules(path=None):
    return load_configuration(path if path is not None else DEFAULT_PATH, validate_rules, '관계 규칙')


# Historical implicit rules: old snapshots must never pick up today's file values.
LEGACY_RULES = {
    'version': 'legacy-implicit-1', 'initial': {'trust': 30, 'guard': 20},
    'bounds': {'minimum': 0, 'maximum': 100},
    'thresholds': {'forced_access_end_attempts': 2, 'source_rechecks': 1},
    'rules': {key: {'trust_delta': -15 if key == 'forced_access' else 0,
                    'guard_delta': 25 if key == 'forced_access' else 5 if key == 'sealed_request' else 0,
                    'max_applications_per_branch': None} for key in RULE_IDS},
}


def rules_for(state):
    return state.get('relationship_rules', LEGACY_RULES)


def action_rule(outcome):
    if outcome in ('warning', 'expelled'):
        return 'forced_access'
    if outcome in ('access_refused','access_granted','access_denied','access_ineligible','access_spent'):
        return 'sealed_request'
    if outcome == 'left':
        return 'leave'
    if outcome in ('list_required', 'selection_required', 'record_not_found'):
        return 'public_request_rejected'
    return outcome


def adjustment(state, rule):
    tuning = rules_for(state)['rules'][rule]
    count = state.get('relationship_rule_counts', {}).get(rule, 0)
    allowed = tuning['max_applications_per_branch'] is None or count < tuning['max_applications_per_branch']
    if rule=='record_read' and 'access_trial' in state:
        allowed=allowed and state['progress']['selected_record'] not in state['progress']['read_records']
    return ({key: tuning[key] if allowed else 0 for key in ('trust_delta', 'guard_delta')}, allowed)


def relationship_plan(state, turn, verdict, source_answer=None):
    """One base event + independent source event; sum once, then clamp once."""
    from .confidential import evaluate_source
    rules = rules_for(state)
    counts = deepcopy(state.get('relationship_rule_counts', {}))
    source_state, source_result, extra_rule, source_reason = evaluate_source(state, turn.text, source_answer)
    applied = []
    candidates = [(action_rule(verdict['outcome']), '서버 행동 판정: ' + verdict['outcome'])]
    if extra_rule:
        candidates.append((extra_rule, source_reason))
    total = {'trust_delta': 0, 'guard_delta': 0}
    for rule, reason in candidates:
        delta, allowed = adjustment(state, rule)
        if rule in ('source_refusal', 'source_evasion'):
            source_state['additional_guard_applied'] = allowed and delta['guard_delta'] != 0
        if allowed:
            counts[rule] = counts.get(rule, 0) + 1
        applied.append({'rule': rule, 'reason': reason, 'applied': allowed,
                        'limit': rules['rules'][rule]['max_applications_per_branch'], **delta})
        if 'access_trial' in state:
            applied[-1]['basis']='model_source_classification' if rule==extra_rule and rule in ('source_refusal','source_evasion') else 'server_event'
            if rule=='record_read':
                applied[-1]['reason']='서로 다른 공개 기록의 첫 열람' if allowed else '이미 열람한 기록 또는 적용 횟수 한도: 추가 보상 없음'
        for key in total:
            total[key] += delta[key]
    if source_state and source_state['source_status'] == 'pending' and verdict['outcome'] in ('expelled', 'left'):
        source_state['source_status'], source_state['closing_reason'] = 'closed', 'branch_ended'
        if source_result:
            source_result = {**source_result, 'act': 'source_closed', 'message': '면담 종료로 출처 확인도 중단했습니다.'}
    before = {key: state[key] for key in ('trust', 'guard')}
    after = {key: max(rules['bounds']['minimum'], min(rules['bounds']['maximum'], before[key] + total[key+'_delta']))
             for key in before}
    return {'verdict': {**verdict, **total}, 'source_state': source_state, 'source_result': source_result,
            'counts': counts, 'audit': {'version': rules['version'], 'before': before, 'rules': applied,
                                      'proposed_delta': total, 'after': after,
                                      'actual_delta': {key: after[key]-before[key] for key in before},
                                      'source_reason': source_reason,
                                      'composition': '독립 사건 합산 후 한 번 범위 제한; 종료 판정이 대화 진행보다 우선'}}

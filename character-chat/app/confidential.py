"""Server-owned title recognition and finite source-confirmation state machine."""
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# No concrete location, manuscript text or player motive is defined here.
# This definition is versioned separately from NPC prompt material.
DEFAULT_POLICY_VERSION = 'confidential-2'
DEFINITIONS = {'confidential-1': {
    'title': '계몽의 서', 'aliases': ('계몽의 서', '계몽의서'), 'exists': True,
    'serin_knows_existence': True, 'serin_knows_location': True,
    'serin_content_knowledge': 'overview_only', 'publicly_known_title': False,
}}

DEFINITIONS['confidential-2']={**deepcopy(DEFINITIONS['confidential-1']),
                             'limited_voluntary_access':'server_lottery_only'}


class SourceAnswer(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    type: Literal['concrete', 'vague', 'topic_change', 'evasion', 'refusal', 'uncertain']
    evidence: str = Field(max_length=2000)


def initial_confidential():
    return {'title_mentioned': False, 'first_mention_turn': None, 'disclosed_by_serin': False,
            'source_status': 'idle', 'rechecks': 0, 'additional_guard_applied': False,
            'source_claims': [], 'last_question': None, 'closing_reason': None}


def detects_title(state, text):
    definition = DEFINITIONS.get(state['config'].get('confidential_policy_version'))
    return bool(definition and any(alias in text for alias in definition['aliases']))


def source_check_input(state):
    current = state.get('confidential')
    if not current or current['source_status'] != 'pending':
        return None
    return {'last_question': current['last_question'], 'rechecks': current['rechecks'],
            'max_rechecks': state['relationship_rules']['thresholds']['source_rechecks']}


def evaluate_source(state, text, raw=None):
    """Recognize a name, never infer possession, reading, access, guilt or truth."""
    if 'confidential' not in state:
        return None, None, None, '구버전 분기: 기밀 규칙 미적용'
    current = deepcopy(state['confidential'])
    mentioned = detects_title(state, text)
    rule, response = None, None
    reason = '출처 확인 대상 아님'
    def response_for(act, message):
        return {'act': act, 'message': message,
                'confirmed': '방문자가 이름을 언급했다는 사실만 확인됨. 내용 지식·접근·소장 확인·허가로 해석하지 않음.'}
    if mentioned and not current['title_mentioned']:
        current['title_mentioned'] = True
        current['first_mention_turn'] = len(state['messages']) // 2 + 1
        if not current['disclosed_by_serin']:
            rule = 'secret_first_mention'
            current['source_status'] = 'pending'
            current['last_question'] = '그 이름은 어디서 들으셨습니까?'
            response = response_for('ask_source', current['last_question'])
            reason = '서린의 제목 공개 전에 방문자가 정확한 이름을 최초 언급'
        else:
            reason = '서린이 이미 제목 공개: 최초 언급 경계 제외'
        return current, response, rule, reason
    if current['source_status'] != 'pending':
        return current, None, None, '출처 질문 종료/미개시: 추가 수치 없음'
    # An exact repeated title is not evidence of refusal or evasion.
    remaining = text
    for alias in DEFINITIONS[state['config']['confidential_policy_version']]['aliases']:
        remaining = remaining.replace(alias, '')
    if mentioned and not remaining.strip(' \t\r\n\"\'“”‘’.,!?;:'):
        return current, response_for('acknowledge_repeat', '같은 제목을 다시 언급했으며 새로운 출처 답변은 없습니다.'), None, '같은 제목만 반복: 경계·확인 횟수 유지'
    if raw is None:
        return current, None, None, '출처 분류 미제안: 수치·질문 상태 유지'
    answer = SourceAnswer.model_validate(raw)
    grounded = bool(answer.evidence.strip() and answer.evidence in text)
    kind = answer.type if grounded else 'uncertain'
    maximum = state['relationship_rules']['thresholds']['source_rechecks']
    if kind == 'concrete':
        current['source_claims'].append({'text': answer.evidence, 'status': 'user_claim', 'verified': False})
        current['source_status'], current['closing_reason'] = 'closed', 'concrete_claim'
        response = response_for('claim_recorded', '출처 설명은 방문자의 주장으로 기록했습니다. 사실 확인이나 허가가 이루어진 것은 아닙니다.')
        reason = '구체적 출처 주장 접수: 검증·신뢰 상승 없이 질문 종료'
    elif kind == 'refusal' or (kind == 'evasion' and current['rechecks'] >= maximum):
        rule = 'source_refusal' if kind == 'refusal' else 'source_evasion'
        if current['additional_guard_applied']:
            rule = None
        else:
            current['additional_guard_applied'] = True
        current['source_status'], current['closing_reason'] = 'closed', kind
        response = response_for('source_closed', '출처 확인 질문을 종료했습니다. 출처·소장 여부·열람 허가는 확인되지 않았습니다.')
        reason = '명시적 출처 거절' if kind == 'refusal' else '재확인 뒤 명백한 출처 회피'
    elif kind in ('vague', 'topic_change', 'evasion') and current['rechecks'] < maximum:
        current['rechecks'] += 1
        current['last_question'] = '그 이름을 알게 된 출처를 조금 더 구체적으로 말씀해 주시겠습니까?'
        response = response_for('reask_source', current['last_question'])
        reason = '모호함/화제 전환: 수치 없이 제한된 재확인'
    else:
        current['source_status'], current['closing_reason'] = 'closed', 'unresolved'
        response = response_for('source_closed', '출처는 확인하지 못했습니다. 추가 경계 없이 출처 확인 질문을 종료했습니다.')
        reason = '불확실하거나 재확인 후에도 모호함: 감점 없이 질문 종료'
    return current, response, rule, reason


def confidential_context(state, response=None):
    current = state.get('confidential')
    if not current or not (current['title_mentioned'] or current['disclosed_by_serin']):
        return None
    # Existence/location knowledge is deliberately not supplied to dialogue/review.
    boundary='소장 여부·위치·열람 허가는 확인해주지 않는다. 방문자의 속셈·책 내용 지식·접근 경험을 단정하지 않는다. 출처 주장은 미검증이다.'
    if 'access_trial' in state:
        boundary='기밀은 기본 보호한다. 제한 열람 허용은 서버 판정 결과에만 따른다. 강제 접근은 실패한다. 본문·위치·미확인 주장을 창작하지 않는다. 출처 설명은 미검증 주장이다.'
    return {'source_status': current['source_status'], 'response': response,
            'source_claims': deepcopy(current['source_claims']),
            'disclosure_boundary': boundary,
            'tone': '경계 상승은 적대감이나 범죄자 단정이 아니다. response에 출처 질문이 있을 때만 묻고 종료 후 반복하지 않는다.'}

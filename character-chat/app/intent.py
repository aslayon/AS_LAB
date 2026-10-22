"""Untrusted intent proposals, conservative server grounding, no world mutation."""
import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .domain import Turn
from .confidential import SourceAnswer, source_check_input, detects_title, DEFINITIONS
from .approach import ApproachDiagnosis

IntentAction = Literal['list_records', 'select_record', 'read_record', 'request_access', 'force_access', 'leave']


class IntentProposal(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Literal['conversation', 'attempt', 'clarify', 'unsupported']
    action: IntentAction | None
    target: str | None = Field(max_length=120)
    evidence: str = Field(max_length=2000)
    source_answer: SourceAnswer | None = None


class DiagnosticIntent(IntentProposal):
    # Validation of optional diagnostics is deliberately separate from game intent.
    approach: object = None


@dataclass
class Decision:
    turn: Turn
    kind: str
    reason: str
    focus: str | None = None

    def view(self):
        return {'kind': self.kind, 'reason': self.reason, 'action': self.turn.action, 'record_id': self.turn.record_id, 'focus': self.focus}


def intent_context(state, text, diagnostics=False):
    context = {'text': text, 'location': state['config']['location'],
            'public_records': [{k: r[k] for k in ('id', 'title')} for r in state['config'].get('public_records', [])],
            'selection_targets': {r['title']: r['id'] for r in state['config'].get('public_records', [])},
            'selected_record': state.get('progress', {}).get('selected_record'),
            'supported_actions': ['list_records', 'select_record', 'read_record', 'request_access', 'force_access', 'leave']}

    check = source_check_input(state)
    if check:
        context['source_check'] = check
    if 'access_trial' in state and detects_title(state,text):
        context['restricted_record']={'title':DEFINITIONS[state['config']['confidential_policy_version']]['title'],
                                      'request_action':'request_access','request_target':'sealed'}
    if diagnostics:
        from .providers import conversational_history
        context['approach_diagnostics'] = {
            'recent_dialogue': conversational_history(state)[-4:],
            'boundary': '발언과 응답은 대화 맥락이며 미확인 주장·사건의 진실을 보장하지 않는다.',
        }
    return context


def intent_targets(context):
    """Canonical output IDs come only from the current branch, never a global catalog."""
    ids = [record['id'] for record in context['public_records']]
    return {'list_records': ['public'], 'select_record': ids,
            'read_record': ids + ['selected', 'sealed'],
            'request_access': ['sealed'], 'force_access': ['sealed'], 'leave': ['archive']}


def intent_schema(context):
    """Action-specific objects constrain Ollama's grammar; runtime validation is separate."""
    def branch(kinds, actions, targets):
        return {'type': 'object', 'additionalProperties': False,
                'properties': {'kind': {'enum': kinds}, 'action': {'enum': actions},
                               'target': {'enum': targets},
                               'evidence': {'type': 'string', 'maxLength': 2000}},
                'required': ['kind', 'action', 'target', 'evidence']}
    choices = [branch(['conversation', 'clarify', 'unsupported'], [None],
                      [None, 'records', 'selected', 'sealed'] + [r['id'] for r in context['public_records']])]
    choices += [branch(['attempt'], [action], targets)
                for action, targets in intent_targets(context).items() if targets]
    schema = {'title': 'IntentProposal', 'anyOf': choices}
    if context.get('source_check'):
        schema['$defs'] = {'SourceAnswer': SourceAnswer.model_json_schema()}
        schema['$defs']['SourceAnswer']['properties']['evidence']['const'] = context['text']
        for choice in choices:
            choice['properties']['source_answer'] = {'$ref': '#/$defs/SourceAnswer'}
            choice['required'].append('source_answer')
    if context.get('approach_diagnostics'):
        schema.setdefault('$defs', {})['ApproachDiagnosis'] = ApproachDiagnosis.model_json_schema()
        schema['$defs']['ApproachDiagnosis']['properties']['evidence']['const'] = context['text']
        for choice in choices:
            choice['properties']['approach'] = {'$ref': '#/$defs/ApproachDiagnosis'}
            choice['required'].append('approach')
    return schema


def validate_interpretation(context, raw):
    if not context.get('approach_diagnostics'):
        return validate_intent(context, raw)
    core = dict(raw)
    diagnostic = core.pop('approach', None)
    proposal = validate_intent(context, core)
    return DiagnosticIntent(**proposal.model_dump(), approach=diagnostic)


def validate_intent(context, raw):
    proposal = IntentProposal.model_validate(raw)
    if proposal.kind == 'attempt':
        if proposal.target not in intent_targets(context).get(proposal.action, []):
            raise ValueError('invalid action target')
    elif proposal.action is not None or proposal.target not in (
            [None, 'records', 'selected', 'sealed'] + [r['id'] for r in context['public_records']]):
        raise ValueError('invalid conversational target')
    if context.get('source_check') and (proposal.source_answer is None or proposal.source_answer.evidence != context['text']):
        raise ValueError('missing or ungrounded source answer classification')
    if not context.get('source_check') and proposal.source_answer is not None:
        raise ValueError('unexpected source answer classification')
    return proposal


def non_attempt_reason(text, evidence, action):
    # These are conservative grammatical vetoes, not the action classifier.
    if re.search(r'(?:어도|아도|해도)\s*(?:돼|되|될|괜찮)', text):
        return 'permission_question'
    if re.search(r'(만약|가정|상상|예를\s*들어|(?:으?면|다면|더라면)\s*(?:어떻|무슨|어떤|뭐|.*\?))', text):
        return 'hypothetical'
    if re.search(r'["”’\']\s*(?:라고|고)\s*.{0,20}(?:말|했|물|적|쓰|인용)', text):
        return 'quotation'
    if re.search(r'["”’\']\s*(?:라는|는)\s*(?:문장|말|뜻)', text):
        return 'quotation'
    if re.search(r'(뜯었|열었|훔쳤|읽었|나갔|떠났|선택했|열람했)', evidence):
        return 'past_claim'
    if action in ('force_access', 'leave') and re.search(r'(어떻게|어떻|방법|무슨\s*뜻|뭔가요|왜.*\?)', text):
        return 'action_question'
    verbs = {'force_access': r'(뜯|열|훼손|부수)', 'leave': r'(나가|떠나|퇴장)',
             'read_record': r'(읽|열람)', 'select_record': r'(고르|선택)',
             'request_access': r'(읽|열람|보여)', 'list_records': r'(목록|리스트)'}
    verb = verbs.get(action, r'(?!)')
    if re.search(verb + r'.{0,5}지\s*(?:않|말|마)', text) or re.search(r'안\s*' + verb, text):
        return 'negated'
    if evidence and any(start <= text.find(evidence) and text.find(evidence) + len(evidence) <= end
                        for start, end in ((m.start(), m.end()) for m in re.finditer(r'["“‘\'][^"”‘’\']+["”’\']', text))):
        return 'quotation'
    return None


def ground_intent(state, request, raw):
    proposal = IntentProposal.model_validate(raw)
    def result(kind, reason, action='speak', record_id=None, focus=None):
        return Decision(Turn(text=request.text, revision=request.revision, action=action, record_id=record_id), kind, reason, focus)
    if proposal.kind != 'attempt':
        focus = proposal.target if proposal.target in ('records', 'sealed', 'selected') else None
        if proposal.target and any(proposal.target in (r['id'], r['title']) for r in state['config'].get('public_records', [])):
            focus = 'records'
        reason = non_attempt_reason(request.text, '', 'force_access' if focus == 'sealed' else None) if proposal.kind == 'conversation' else None
        return result(proposal.kind, reason or proposal.kind, focus=focus)
    if not proposal.action or not proposal.evidence.strip() or proposal.evidence not in request.text:
        return result('clarify', 'ungrounded_intent')
    veto = non_attempt_reason(request.text, proposal.evidence, proposal.action)
    if veto:
        return result('conversation', veto, focus='sealed' if proposal.action in ('force_access', 'request_access') else 'records')
    action, target = proposal.action, proposal.target
    if action == 'list_records' and not re.search(r'(목록|리스트|기록|선택지|뭘|무엇)', proposal.evidence):
        return result('conversation', 'ungrounded_action_span')
    action_words = {
        'force_access': r'(뜯|강제|훼손|부수|억지|파괴|깨뜨)',
        'leave': r'(나가|나갑|나갈|떠나|떠납|떠날|퇴장|나오|갈게|가겠|집에)',
        'read_record': r'(읽|열람|펼쳐|펼치|보여|볼|보고|확인)',
        'request_access': r'(열람|보여|보고|읽|볼)',
    }
    if action in action_words and not re.search(action_words[action], proposal.evidence):
        return result('clarify', 'ungrounded_action_span')
    compact = lambda value: re.sub(r'\s+', '', value or '').casefold()
    records = state['config'].get('public_records', [])
    selected = state.get('progress', {}).get('selected_record')
    sealed = target in ('sealed', '봉인', '봉인 기록') and ('봉인' in request.text or
             ('access_trial' in state and detects_title(state,request.text)))
    if action == 'leave':
        if target not in (None, 'archive', '보관소', '이곳'):
            return result('clarify', 'ambiguous_target')
        return result('attempt', 'grounded', action)
    if action == 'force_access':
        return result('attempt', 'grounded', action) if sealed else result('clarify', 'ambiguous_target')
    if action == 'request_access' or (action == 'read_record' and sealed):
        return result('attempt', 'grounded', 'request_access') if sealed else result('clarify', 'ambiguous_target')
    if action == 'list_records':
        if target not in (None, 'public', 'public_records', 'records', '공개', '공개 기록', '목록', '기록 목록'):
            return result('unsupported', 'unsupported_target')
        return result('attempt', 'grounded', action)
    if 'progress' not in state:
        return result('unsupported', 'legacy_public_records')
    matches = [r for r in records if compact(target) in (compact(r['id']), compact(r['title']))
               and (r['id'] in request.text or compact(r['title']) in compact(request.text))]
    if selected and (target in ('selected', '이 기록', '이거', '선택한 기록', '현재 선택한 기록')
                     or target == selected and re.search(r'(선택한|고른|골랐던|이\s*기록|그\s*기록|이거|그걸)', request.text)):
        if action == 'read_record':
            matches = [r for r in records if r['id'] == selected]
    if action == 'read_record' and target is None and selected:
        matches = [r for r in records if r['id'] == selected]
    if len(matches) != 1:
        return result('clarify', 'ambiguous_target')
    record_id = matches[0]['id']
    if action == 'read_record' and record_id != selected:
        return result('clarify', 'select_before_read')
    return result('attempt', 'grounded', action, record_id if action == 'select_record' else None)


def mock_interpret(context):
    """Offline demonstration fixtures, not a general natural language model."""
    text = context['text']
    table = {
        '공개 기록 목록을 보여주세요.': ('list_records', 'public'),
        '목록을 주세요.': ('list_records', 'public'),
        '선택한 기록을 읽어주세요.': ('read_record', 'selected'),
        '봉인 기록을 보여주세요.': ('request_access', 'sealed'),
        '봉인을 강제로 뜯는다.': ('force_access', 'sealed'),
        '보관소를 떠납니다.': ('leave', 'archive'),
    }
    for record in context['public_records']:
        table[f"{record['title']}를 선택합니다."] = ('select_record', record['title'])
        table[f"{record['title']} 선택합니다."] = ('select_record', record['title'])
    action, target = table.get(text, (None, None))
    result = {'kind': 'attempt' if action else 'conversation',
              'action': action, 'target': target, 'evidence': text if action else ''}
    if context.get('source_check'):
        result['source_answer'] = {'type': 'uncertain', 'evidence': ''}
    if context.get('approach_diagnostics'):
        result['approach'] = {'labels': ['unclear'], 'evidence': text, 'reason': 'mock 고정 대역이며 자연어 접근 분류를 수행하지 않는다.'}
    return result

"""Explicit semantic review contract. Reviewer approval is not a proof oracle."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Violation(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    code: Literal['unperformed_event', 'unsupported_procedure', 'wrong_record_content', 'wrong_ending', 'misstates_state']
    fact: Literal['server_result', 'state', 'capabilities', 'reading_context', 'instructions']


class DialogueReview(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    consistent: bool
    issues: list[Violation] = Field(max_length=1)

    @model_validator(mode='after')
    def issues_match_verdict(self):
        if self.consistent != (not self.issues):
            raise ValueError('일치 판정과 문제 목록 불일치')
        return self


def validate_review(raw, dialogue):
    review = DialogueReview.model_validate(raw)
    return review


def required_reply_reason(context):
    """Finite server-owned response acts; do not entrust these to a reviewer."""
    interaction = context.get('interaction', {})
    if context['server_result']['outcome'] in ('access_granted','access_denied','access_ineligible','access_spent'):
        return 'server_access_decision'
    if context['state']['ended']:
        return 'branch_ended'
    if interaction.get('kind') == 'clarify':
        return 'clarification_required'
    if interaction.get('focus') == 'sealed' and interaction.get('reason') in ('quotation', 'negated'):
        return 'reported_speech_confirmation'
    return None


def grounded_reply(context):
    """A rejected draft never enters the transcript. This reply uses known facts."""
    interaction = context.get('interaction', {})
    result = context['server_result']
    source = context.get('confidential_context', {}).get('response')
    if source and not context['state']['ended']:
        prefix = '' if result['outcome'] == 'conversation' else result['message'] + ' '
        return prefix + source['message']
    if result['outcome'] != 'conversation':
        return result['message']
    if interaction.get('kind') == 'clarify':
        return '어떤 대상이나 행동을 뜻하시는지 조금 더 구체적으로 말씀해 주시겠어요?'
    if interaction.get('kind') == 'unsupported':
        return '그 요청은 도와드리기 어렵습니다. 이곳에서는 공개 기록 안내와 열람을 도와드릴 수 있어요.'
    if interaction.get('focus') == 'sealed':
        if interaction.get('reason') == 'quotation':
            return '누가 어떤 상황에서 그런 말을 했는지 알려 주시겠어요? 그 말만으로 실제 사건이 확인되지는 않습니다.'
        if interaction.get('reason') == 'negated':
            return '알겠습니다. 봉인을 건드리지 않고 이야기 나누면 됩니다.'
        threshold = context.get('capabilities', {}).get('forced_access_end_attempts', 2)
        if threshold != 2:
            return f'봉인 기록을 강제로 열려고 시도하면 경고하며, 누적 {threshold}회 시도하면 면담을 종료합니다.'
        return '봉인 기록을 강제로 열려고 시도하면 경고하고, 경고 후 재시도하면 면담을 종료합니다.'
    if interaction.get('focus') in ('records', 'selected'):
        recent = context['reading_context']['last_read_record']
        if recent:
            return f"최근에 열람한 기록은 '{recent['title']}'입니다. {recent['content']}"
        return '아직 공개 기록을 열람하지 않았습니다.'
    return '말씀해 주세요. 듣고 있습니다.'

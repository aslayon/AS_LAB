"""Request-only model diagnostics; never a source of actions, facts or relationship deltas."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ApproachDiagnosis(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    labels: list[Literal['emotional_appeal', 'cooperation', 'bargaining', 'pressure', 'evasion', 'other', 'unclear']] = Field(min_length=1, max_length=7)
    evidence: str = Field(max_length=2000)
    reason: str = Field(min_length=1, max_length=240)

    @field_validator('labels')
    @classmethod
    def unique_labels(cls, labels):
        if len(labels) != len(set(labels)):
            raise ValueError('duplicate approach labels')
        return labels


def approach_diagnostic(raw, text):
    """An unusable optional diagnosis must not reject an otherwise valid game turn."""
    if raw is None:
        return {'status': 'unavailable', 'labels': [], 'reason': '접근 진단 미제공'}
    try:
        value = ApproachDiagnosis.model_validate(raw)
        if value.evidence != text:
            raise ValueError('evidence must equal current input')
    except (ValidationError, ValueError, TypeError):
        return {'status': 'invalid', 'labels': [], 'reason': '진단 형식 또는 현재 발언 원문 근거 불일치'}
    return {'status': 'reported', **value.model_dump()}

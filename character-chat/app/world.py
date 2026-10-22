"""Validate NPC-safe background data; confidential definitions stay in server code."""
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from .configuration import load_configuration

DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'config' / 'world.json'
Text = Annotated[str, StringConstraints(strict=True, min_length=1, pattern=r'\S')]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class PublicRecord(StrictModel):
    id: Annotated[str, StringConstraints(min_length=1, max_length=80, pattern=r'^[a-z0-9][a-z0-9._-]*$')]
    title: Text
    content: Text


class World(StrictModel):
    version: Annotated[str, StringConstraints(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9._-]+$')]
    character: Text
    location: Text
    environment: Text
    known_facts: list[Text] = Field(min_length=1)
    dialogue_guidelines: list[Text] = Field(min_length=1)
    judgment_guidelines: list[Text] = Field(default_factory=list)
    # Existing consumers use core[0] as personality and derive core[-1] from tuning.
    core: list[Text] = Field(min_length=2)
    public_records: list[PublicRecord] = Field(min_length=1)
    first_dialogue: Text

    @field_validator('public_records')
    @classmethod
    def unique_records(cls, records):
        for field in ('id', 'title'):
            seen = set()
            for index, record in enumerate(records):
                value = getattr(record, field)
                if value in seen:
                    raise ValueError(f'public_records.{index}.{field}: 중복 값 {value}')
                if field == 'id' and value in ('public', 'selected', 'sealed', 'archive', 'records'):
                    raise ValueError(f'public_records.{index}.id: 예약된 대상 ID {value}')
                seen.add(value)
        return records


def validate_world(value):
    return World.model_validate(value).model_dump(exclude_unset=True)


def load_world(path=None):
    return load_configuration(path if path is not None else DEFAULT_PATH, validate_world, '배경')

"""Strict UTF-8 JSON loading shared by editable game configuration files."""
import json
from pathlib import Path


def load_configuration(path, validate, label):
    path = Path(path).resolve()

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'항목 {key}: 중복 키')
            result[key] = value
        return result

    try:
        return validate(json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique))
    except (OSError, ValueError) as error:
        raise ValueError(f'{label} 설정 오류 ({path}), 항목 $: {error}') from None

# 배경·관계 설정 편집 안내

2026-10-22 · 015 access-ending. 배경·일반 판단 기준·개발용 진단 위에 서버 확률 판정과 고정 결말을 추가했다. [새 자격/확률/결말/기록 전체 안내](access-rules.md)를 함께 본다.

직접 편집할 파일은 [config/world.json](../config/world.json)과 [config/relationship_rules.json](../config/relationship_rules.json)이다. UTF-8 JSON으로 저장한다. 주석·마지막 쉼표·중복 키는 허용하지 않는다. 설정을 편집한 뒤 **게임 서버 재시작 → 브라우저 새로고침 → 새 게임** 순서로 적용한다.

## 배경 항목과 예시

현재 새 게임 버전은 `archive-5.0`이며 기밀의 자발적 제한 열람 예외를 명시한다. 이전 분기는 당시 실제 값을 유지한다. 아래 예시는 변경할 항목의 일부만 보여 준다. 전체 파일을 예시 조각으로 대체하지 않는다.

| 항목 | 의미·수정 예시 | 검증·사용 지점 |
| --- | --- | --- |
| `version` | 실험 구분. 예: `archive-4.0-detail-b` | 영문·숫자·점·밑줄·하이픈, 1–80자. `config_version`과 설정 본문에 저장 |
| `character` | 캐릭터 이름. 예: `서린` | 비어 있지 않은 문자열. `character_instructions()`에서 기존 생성 경로에 전달 |
| `core[0]` | 성격. 예: `서린은 조용하고 신중한 기록 보관인이다.` | 기존 모델의 personality와 화면 인물 설명이 이 위치를 참조. 첫 항목 위치 유지 |
| `location` | 장소. 예: `골목 끝의 작은 기록 보관소` | 화면·의도 해석·대사 생성 자료 |
| `environment` | 시간·날씨·주변 분위기. 예: `비가 내리는 늦은 밤.` | 화면·대사 생성/검토 자료. 의도 입력 전체에 새로 추가하지 않음 |
| `known_facts` | NPC가 이미 아는 사실의 문자열 배열 | 최소 1개. 예: `["이곳은 방문 기록과 장부를 보관한다."]` |
| `dialogue_guidelines` | 말투·응답 방법의 문자열 배열 | 최소 1개. 예: `["질문에 먼저 답하고 필요한 경우에만 되묻는다."]` |
| `judgment_guidelines` | 기록 보호·사정 청취·공감/믿음/허용 분리·협조/일관성·압박/회피·공개 대안·미구현 절차 금지 | 비어 있지 않은 문자열 배열. 구버전 호환을 위해 항목 생략 가능하며 옛 분기에 주입하지 않음 |
| `core[1:]` | 기존 핵심 규칙의 설명 | `core` 전체 최소 2개. 문구 편집이 서버의 판정 규칙을 바꾸지는 않음 |
| `core`의 마지막 항목 | 강제 접근 횟수 규칙을 위한 기존 자리 | `initial_state()`가 관계 설정의 `forced_access_end_attempts`로 실제 문구를 생성한다. 종료 횟수는 관계 JSON에서 수정 |
| `public_records` | 공개 기록 객체 배열 | 최소 1개. 현재 3개이며 개수 자체를 3으로 고정하지 않음 |
| `public_records[i].id` | 기록을 식별하는 코드용 ID | 1–80자, 소문자 영문·숫자로 시작하고 이후 소문자·숫자·점·밑줄·하이픈. 배열 내 중복 금지 |
| `public_records[i].title` | 목록·선택에 쓰는 공개 제목 | 비어 있지 않은 문자열, 중복 금지. 예: `방문 기록` |
| `public_records[i].content` | 열람할 고정 본문 | 비어 있지 않은 문자열. 열람 전에는 전체 본문을 모델에 주지 않는 기존 경계를 유지 |
| `first_dialogue` | 새 게임 첫 대사 | 비어 있지 않은 문자열. `messages[0].content`로 복사. 매 턴 프롬프트에 재주입하지 않음 |

문자열에는 공백 외의 글자가 있어야 하고, 숫자·불리언을 문자열 대신 넣을 수 없다. 정의되지 않은 필드는 거절한다. `core[0]`과 마지막 항목을 빼고 상세 규칙 설명을 추가하려면 그 사이에 넣는다.

배경 상세도 비교는 `location`, `environment`, `known_facts`, `dialogue_guidelines`, 필요하면 `core[0]`, `judgment_guidelines`를 바꾸면 된다. 한 실험에서 관계 수치를 고정하면 배경의 영향을 비교하기 쉽다. 예를 들어 간단한 환경 `비가 내리는 늦은 밤.`과 상세한 환경 `비가 내리는 늦은 밤. 접견대에는 장부가 펼쳐져 있고, 빗소리가 문밖에서 들린다.`를 비교할 수 있다. 상세화할 때 새로 쓴 관찰을 NPC가 아는 일반 사실로 제공한다는 점을 고려한다.

이름·설명을 JSON에서 읽는 경로로 연결했지만, 화면의 고정 제목/화자 표시와 일부 특수 프롬프트·서버 대체문에는 기존 `서린`·성격 표현이 남아 있다. 이번 작업은 기존 문구·입력을 보존하는 분리이며, 이름 변경만으로 앱 전체의 인물이 자동 교체되는 기능은 아니다. 배경을 길게 늘리면 기존 모델 문맥 예산을 넘을 수도 있다. 모델의 오판·대사 품질도 설정 검증과 별개다.

## 관계 항목과 비교 방법

[기존 조정표](relationship-rules.md)의 값·범위·규칙 ID를 유지한다. 현재 관계 JSON 버전은 `relationship-2.0`이며 구버전 값은 각 snapshot에 보존한다.

| 항목 | 의미·수정 예시 |
| --- | --- |
| `version` | 실험 이름. 예: `relationship-start-high`. 배경 버전과 독립 |
| `initial.trust`, `initial.guard` | 새 게임 초기 신뢰·경계. 기본 30/20. 초기 관계 비교 예: `{"trust":60,"guard":10}` |
| `bounds.minimum`, `bounds.maximum` | 최종 수치 제한. 기본 0/100. 0–100 안의 정수이며 최소 < 최대, 초기값도 범위 안이어야 함 |
| `rules.<ID>.trust_delta`, `guard_delta` | 해당 사건의 증감량. −100…100 정수. 예: `sealed_request.guard_delta`를 5에서 2로 변경 |
| `rules.<ID>.max_applications_per_branch` | 분기별 수치 적용 횟수. `null`은 제한 없음, 0은 수치 적용 안 함, 일반 규칙은 0…10000 |
| `thresholds.forced_access_end_attempts` | 강제 접근 종료 시도 횟수. 기본 2, 2…100 정수 |
| `thresholds.source_rechecks` | 출처 재확인 최대 횟수. 기본 1, 1…3 정수 |

`secret_first_mention`, `source_refusal`, `source_evasion`의 수치 반복 한도는 기존처럼 0 또는 1만 허용한다. 수치 적용을 꺼도 사건·출처 확인·행동 자체를 끄는 것은 아니다. 여러 사건의 증감은 합산 후 범위를 한 번 적용한다.

| 규칙 ID | 적용 사건 | 기본 신뢰/경계 증감 |
| --- | --- | --- |
| `conversation` | 일반 발언 | 0 / 0 |
| `catalog_listed` | 공개 목록 확인 | 0 / 0 |
| `record_selected` | 공개 기록 선택 | 0 / 0 |
| `record_read` | 공개 기록 첫 열람 (서로 다른 ID, 기본3회) | +10 / −5 |
| `public_request_rejected` | 목록·선택 선행 조건 미충족, 잘못된 기록 ID | 0 / 0 |
| `sealed_request` | 자발적 기밀 열람 요청 (구버전은+5) | 0 / 0 |
| `forced_access` | 강제 접근 경고·종료 | −15 / +25 |
| `leave` | 자발적 퇴장 | 0 / 0 |
| `secret_first_mention` | 기밀 제목 최초 언급 | 0 / +10 |
| `source_refusal` | 출처 답변 명시적 거절 | 0 / +5 |
| `source_evasion` | 재확인 뒤 출처 회피 | 0 / +5 |

초기값 비교는 `initial`만, 증감량 비교는 `rules` 안의 delta만 변경한다. 반복 제한이나 임계치까지 함께 바꾸면 다른 실험 조건이 된다. 숫자 변경 시 이 안내와 `relationship-rules.md`의 실험 기록도 함께 남기는 것이 좋다. 실제 모델의 출처 분류는 오판할 수 있어, 같은 숫자라도 어떤 사건으로 해석됐는지 개발 패널에서 확인한다.

## 문구와 ID의 차이

장소·환경·알려진 사실·성격·대화 지침·공개 제목/본문·첫 대사는 편집할 수 있는 문구다. 핵심 규칙 문구만 바꿔도 서버 판정은 바뀌지 않는다. 제한 열람은 access_policy와 예약/검증을 거치며 강제 접근은 실패하므로 코드와 모순된 지침을 쓰지 않는다.

공개 기록 ID는 현재 분기의 목록, `selection_targets`, 의도 스키마, 선택/열람 상태가 참조한다. 새 게임에서는 수정한 ID를 동적으로 사용하고 옛 게임은 저장된 ID를 사용한다. 단순 문구 비교에서는 ID를 유지한다. `public`, `selected`, `sealed`, `archive`, `records`는 예약 대상이므로 기록 ID로 쓸 수 없다.

관계 규칙 ID 11개와 JSON 키 이름은 코드가 참조한다. 이름을 바꾸거나 규칙을 추가/삭제하면 검증 오류가 난다. 행동 ID(`speak`, `list_records` 등), outcome, 표정 enum, 기밀 정책 ID는 이번 편집 대상이 아니다. 버전명은 비교용 표지이며 동일 버전일 때 파일 내용을 공유하는 참조 키가 아니다.

## 일반 배경과 기밀·플레이어 정보

`world.json`에는 NPC에게 줄 수 있는 일반 배경만 넣는다. 이 파일의 내용은 모델·게임 화면에 전달될 수 있다. 스키마가 문자열 안의 비밀을 의미적으로 판별해 숨겨 주지는 않는다.

- 기밀의 실존·서린의 지식 범위는 [app/confidential.py](../app/confidential.py)의 `DEFINITIONS`에 유지한다. `confidential_policy_version`도 서버에서 연결하며 배경 JSON에는 두지 않는다.
- 플레이어의 숨은 목적·작가 메모는 [docs/scenario.md](scenario.md)에 둔다. 런타임이 이 문서를 읽지 않는다.
- `character_instructions()`는 명시한 일반 캐릭터 항목과 `judgment_guidelines`만 골라 전달한다. 공개 기록은 목록에서 ID·제목만 전달하고, 실제 열람 때 기존 `reading_context()`와 서버 결과로 본문을 전달한다.
- 의도 입력은 기존 장소·목록·선택 상태·지원 행동과 진행 중 출처 질문을 사용한다. 개발 모드 자유 입력의 접근 진단에는 현재 분기의 검토된 대화 맥락 최근 4개 메시지를 추가하며 사실 근거로 취급하지 않는다. 모델에는 미등장 기밀 제목/실존/위치를 새로 전달하지 않는다.

## trust/guard가 실제로 쓰이는 곳

trust/guard는 기존 게임 관계 수치이며 별도의 호감도 변수는 없다. 새 게임에서는 제한 열람의 자격 조건과 성공 확률에도 사용한다. 숫자만으로 허가가 확정되지는 않으며 실제 요청과 서버 판정이 필요하다. 아래는 현재 코드의 사용 범위다.

| 구분 | 수치가 영향을 주는 부분 | 수치가 직접 결정하지 않는 부분 | 코드 근거 |
| --- | --- | --- | --- |
| 초기값·저장·화면 | 초기 신뢰/경계, 사건 delta 합산, 범위 제한, 요약과 미터 표시 | 수치만으로 사건을 생성하지 않음 | `domain.initial_state/advance_state`, `relationship.relationship_plan`, `static/app.js:render` |
| 의도 해석 | 입력에 trust/guard 자체를 넣지 않음. 개발 모드의 접근 진단도 수치 입력·판정은 아님 | 높고 낮음으로 서버의 행동 해석을 바꾸는 분기 없음 | `intent.intent_context`, `ollama_provider.interpret` |
| 대사 생성 | `build_context()`의 판정 후 state, 일반 잡담의 relationship 및 일반 행동 경로에 전달. 말투에 확률적으로 영향을 줄 수 있음 | 모든 생성 경로가 절대 수치를 받는 것은 아님. 되묻기·봉인 인용/가정·기밀 출처 전용 초안은 선별 자료와 verdict 사용. 수치별 고정 말투 임계치 없음 | `providers.build_context`, `ollama_provider.payload/dialogue_payload` |
| 대사 검토 | state의 신뢰/경계가 검토 자료에 포함. 기밀 경로도 해당 수치를 유지 | 숫자로 접근 허가를 새로 만들지 않음. 같은 모델의 검토이며 정확성 보장 아님 | `ollama_provider.review` |
| 표정 | 사건 결과가 `차분`·`경계`·`단호`를 지정하고 제안을 대조 | guard가 높아서 자동으로 `경계`가 되거나 trust가 높아서 `온화`가 되지 않음 | `domain.resolve/apply_turn` |
| 공개 기록·봉인 공개 | 새 게임에서 trust/guard는 제한 열람 자격·확률에 사용 | 공개는 목록→선택→열람. 기밀은 조건+실제 요청+서버 추첨 성공 필요. 숫자나 모델 선언만으로 열리지 않음. 강제 접근 실패 | `access.eligibility/probability/reserve/apply_decision`, `domain.advance_state` |
| 기밀 정보·출처 질문 | 사건에 따라 관계 delta가 적용됨. 추가 가산 적용 여부를 기록 | 질문 개시·재확인·종료는 제목 언급·출처 유형·횟수 상태에 따름. guard 값 자체의 공개 임계치 없음 | `confidential.evaluate_source/confidential_context`, `relationship.relationship_plan` |
| 면담 종료 | 종료 행동과 함께 해당 사건의 delta 적용 | trust=0 또는 guard=100만으로 종료하지 않음. 강제 접근 누적 횟수·`leave` 또는 서버 제한 열람 성공으로 종료 | `domain.resolve/advance_state` |

## 로딩·오류·저장과 복원

`create_app()`이 `load_world()`와 `load_rules()`를 호출해 파일을 한 번 읽는다. `configuration.load_configuration()`은 UTF-8·JSON 구문·중복 키를, 각 Pydantic 모델은 필수 항목·엄격한 타입·중복 ID/제목 등을 검증한다. 실패하면 DB를 열기 전에 서버 시작을 중단하며 절대 파일 경로와 항목을 포함한 `ValueError`를 출력한다. 예: `배경 설정 오류 (/.../config/world.json), 항목 $: ... public_records.0.content ...`. JSON 구문 오류는 루트 `$`와 행/열을 표시한다. 관계 설정의 복합 오류는 `bounds`, `initial`, `rules` 등 해당 제약을 함께 설명한다.

새 게임에는 원본 배경의 전체 값·버전을 `world_settings`, 게임에 적용할 배경을 `config`/`config_version`, 관계 전체 값·버전을 `relationship_rules`에 깊은 복사로 저장한다. `config`는 기존처럼 강제 접근 안내의 마지막 core 문구를 관계 임계치로 계산하고 서버의 기밀 정책 ID를 포함한다. 편집 원문은 `world_settings`에 그대로 남아 이 계산과 구분된다. 원본 설정 전체를 모델에 통째로 전달하지 않는다.

기존 게임·체크포인트·회귀는 저장된 전체 snapshot을 사용한다. 현재 JSON을 다시 읽거나 버전명으로 새 값을 주입하지 않는다. **같은 버전 문자열로 내용을 수정해도 옛 분기는 바뀌지 않는다.** 분리 전 `world_settings`/`first_dialogue`가 없던 분기도 그대로 읽고 복원한다. 아주 오래된 관계 규칙 미저장 분기는 기존 `LEGACY_RULES`를 사용한다. 기존 DB 삭제나 마이그레이션은 필요 없다.

## 적용 명령

1. 두 JSON 파일을 편집·저장한다.
2. 게임 서버 터미널에서 `Ctrl+C`로 종료한다. 배경·관계 변경만으로 Ollama 서버를 재시작할 필요는 없다.
3. 게임 서버를 다시 실행한다. JSON 변경 감지에 의존하지 않도록 아래 명령에는 `--reload`를 쓰지 않는다.

```bash
cd ~/projects/character-chat
CHARACTER_CHAT_PROVIDER=ollama \
OLLAMA_MODEL=exaone3.5:7.8b-instruct-q4_K_M \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Ollama가 꺼져 있으면 별도 터미널에서 `cd ~/projects/character-chat` 후 `bash scripts/serve_ollama.sh`로 실행한다. 고정 응답 비교용 mock은 다음처럼 실행한다.

```bash
cd ~/projects/character-chat
CHARACTER_CHAT_PROVIDER=mock \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

4. <http://localhost:8000>을 새로고침하고 **새 게임**을 누른다. 기존 분기를 계속하면 이전 설정으로 진행한다.

개발 패널은 명령에 `CHARACTER_CHAT_DEV=true`를 추가하면 켤 수 있다. 실제 게임 설정·전후 수치·증감 근거와 모델 초안/최종을 구분해서 비교한다. `.env` 자동 로딩은 없다.

## 접근 방식 실험과 진단 (014)

`judgment_guidelines`는 특정 가족·질병·사연의 사실을 정의하는 항목이 아니다. 사용자의 사정을 들을 수 있다는 성격 기준이며, 공감·주장에 대한 믿음·기록 접근 허용을 분리한다. 014 당시 배경 버전명은 archive-4.0을 유지했고 현재는 archive-5.0이다. 전체 실제 값과 원본을 저장하므로 기존 게임에 이 기준을 주입하지 않는다. 새 기준 비교에는 재시작과 새 게임이 필요하다.

`CHARACTER_CHAT_DEV=true`로 실행한 **자유 입력**에서는 기존 의도 호출에서 접근도 기록한다. 개발 패널/API의 `debug.approach`에 `status`, `labels`, `evidence`, `reason`을 표시한다. 라벨은 `emotional_appeal`, `cooperation`, `bargaining`, `pressure`, `evasion`, `other`, `unclear`이며 복합적이면 여러 개를 허용한다. `reported`는 형식과 현재 원문 근거가 맞는 모델 보고라는 뜻이며 의미적 정답 표시가 아니다. 미제공은 `unavailable`, 잘못된 진단은 `invalid`로 남기고 정상 게임 의도를 거절하지 않는다. 게임 의도·제안·검토 자체의 오류는 기존처럼 턴 전체를 저장하지 않는다.

진단 라벨/이유는 행동·신뢰/경계·표정·정보 공개·종료 판정에 전달하지 않고, 대사 입력과 저장된 메시지/기억/체크포인트에도 넣지 않는다. 대사는 현재 발언·대화 맥락·설정의 일반 판단 기준을 받는다. 의도/대사/검토 호출은 free 3회, direct 2회를 유지한다. mock의 진단은 `unclear` 고정 대역이며 자연어 이해 결과가 아니다. 개발 모드가 꺼져 있거나 direct면 새 접근 진단을 요청하지 않는다.

기존 source_answer 출처 유형 분류와 수치 규칙은 유지하며 새 접근 진단과 다르다. [실제 비교 원문·잠정 검토](reports/014-approaches.md)와 [실패 사례](failure-cases/014-approaches.md)를 본 뒤 사용자가 수치 연결 여부를 결정한다. 현재는 수치 연결 없음이다.

## 자발적 열람 확률·고정 결말·자동 저장 (015)

`relationship_rules.json.access_policy`에서 신뢰/경계 자격, 공개 기록 최소 수, 제목/출처/강제 접근 조건, 확률 기본값·계수·상하한을 수정한다. 초기30/20 → 공개 첫 열람2개+제목 인지+질문 종료50/20이면50%, 3개60/15이면62.5%다. 첫 열람 보상은 rules.record_read(+10/−5/최대3회)이며 재열람·인사·칭찬은 보상하지 않는다. 모델 접근 라벨은 계속 수치에 연결하지 않는다.

`config/ending.json`의 version/title/body는 서버 전용 결말 원본이다. **본문을 world.json이나 NPC known_facts로 옮기지 않는다.** 새 게임의 비공개 DB 설정에 실제 값을 복사하며, 같은 버전명 수정/재시작으로 기존 게임 본문을 바꾸지 않는다. 서버 성공 후 고정 본문을 표시하고 종료한다. 자격·식·확률 범위·재전송/회귀/저장 복구/다운로드 설명과 적용 명령은 [access-rules.md](access-rules.md)에 있다.

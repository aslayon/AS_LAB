# Ollama 로컬 연결과 실행

현재 단계는 **015 · access-ending**다. EXAONE은 유지하며 서버 제한 열람 확률·고정 결말·자동 기록을 추가했다. [확률/자격/수치·적용·다운로드](access-rules.md), [실제3게임 원문·중간 실패·저장 대조](reports/015-access.md), [최신 구조](architecture.md)를 먼저 본다. 아래 모델 비교·측정은 과거 단계의 기록이다.

이 프로젝트는 기본 **mock** 모드를 유지하고, 실행할 때 환경변수로 Ollama를 선택한다. 실제 모델 후보·GPU·성능과 검증 결과는 이 문서 및 [변경 기록](changes.md)에 구분해 남긴다.

## 실행 — 터미널 두 개

Ollama 서버를 실행할 WSL 터미널:

```bash
cd ~/projects/character-chat
bash scripts/serve_ollama.sh
```

다른 WSL 터미널에서 게임 실행:

```bash
cd ~/projects/character-chat
CHARACTER_CHAT_PROVIDER=ollama \
OLLAMA_MODEL=exaone3.5:7.8b-instruct-q4_K_M \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

<http://localhost:8000>에서 Ctrl+Shift+R로 새로고침한다. 화면에 설정된 생성기·모델명이 표시되고, 성공한 Ollama 턴에는 생성에 걸린 시간이 표시된다. 생성기 설정을 바꾸면 게임 서버를 재시작한다.

mock으로 실행하려면 Ollama 서버 없이 다음을 사용한다.

```bash
cd ~/projects/character-chat
CHARACTER_CHAT_PROVIDER=mock \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

`GET /api/health`는 설정된 생성기와 모델을 알려 준다. mock의 모델은 `null`이다. 이 health는 게임 앱 상태이며 Ollama 접속이나 GPU 추론 성공을 보장하는 검사가 아니다.


기존 Qwen으로 실행할 때는 위 명령의 모델만 바꾼다. 기존 가중치와 실험 기록은 보존돼 있다.

```bash
CHARACTER_CHAT_PROVIDER=ollama OLLAMA_MODEL=qwen3:4b-instruct-2507-q4_K_M \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

셸에 이전 `OLLAMA_MODEL`이 export돼 있으면 그 값이 기본값보다 우선한다. EXAONE 명령은 모델을 명시해 이 혼동을 피한다. `.env.example`은 안내 파일이며 `.env` 자동 로딩은 없다.

## 설치 위치와 시스템에 미치는 영향

- 공식 Linux 배포본을 프로젝트 `.runtime/ollama/`에 압축 해제했다. 실행 파일은 `.runtime/ollama/bin/ollama`다.
- 모델 저장 위치는 `.runtime/models/`. 서버 스크립트가 `OLLAMA_MODELS`를 이 경로로 지정한다.
- `127.0.0.1:11434`에만 수동 실행하고 `OLLAMA_NO_CLOUD=1`로 클라우드 기능을 끈다.
- 시스템 Python·드라이버·WSL 설정·셸 프로필·자동 시작 서비스는 변경하지 않았다. sudo와 시스템 설치 스크립트는 사용하지 않았다.
- Ollama가 최초 서버 실행 중 `~/.ollama`에 자체 키를 생성했다. 키 내용은 Git에 포함하지 않는다.
- 본체 압축 다운로드는 약 1.44GB, 해제 후 관측 크기는 약 2.2GiB였다. 압축 파일은 해제 후 제거했다.
- 시험용 `qwen3:4b`와 최종 후보 `qwen3:4b-instruct-2507-q4_K_M`는 서로 다른 약 2.5GB 가중치다. 두 모델을 내려받으면 모델 공간도 그만큼 추가로 필요하다.
- 004 당시 `.runtime/` 관측 크기는 **약 6.8GiB**였다. 이번 EXAONE 7.8B/Qwen3 14B 후보 다운로드로 가중치 약 14.05GB를 추가했고 모델 저장소는 약 18GiB다. 기존 가중치와 후보는 모두 보존한다.
- `.runtime/` 전체는 Git 제외 대상이므로 다른 환경에 Git 코드만 복사하면 본체·모델은 별도 설치해야 한다. 유료 API는 사용하지 않는다.

재설치가 필요할 때의 수동 절차다. 아래는 네트워크 다운로드와 프로젝트 내부 파일 생성을 수행한다. 실행 전 용량과 설치 위치를 확인한다. Python 3.14의 zstd 지원을 사용한다.

```bash
cd ~/projects/character-chat
mkdir -p .runtime/ollama
curl -fL https://ollama.com/download/ollama-linux-amd64.tar.zst -o .runtime/ollama-linux-amd64.tar.zst
.venv/bin/python - <<'PY'
from compression import zstd
from pathlib import Path
import tarfile
archive = Path('.runtime/ollama-linux-amd64.tar.zst')
with zstd.open(archive, 'rb') as stream, tarfile.open(fileobj=stream, mode='r|') as tar:
    tar.extractall('.runtime/ollama', filter='data')
archive.unlink()
PY
bash scripts/serve_ollama.sh
```

서버가 실행된 뒤 다른 터미널에서 모델 다운로드:

```bash
cd ~/projects/character-chat
OLLAMA_HOST=127.0.0.1:11434 \
.runtime/ollama/bin/ollama pull qwen3:4b-instruct-2507-q4_K_M
```

공식 배포 경로는 시간이 지나면 본체 버전·크기가 달라질 수 있다. 이번에 실제 설치한 버전은 **0.40.6**이다. [공식 Linux 안내](https://docs.ollama.com/linux)

## 모델 후보와 선택 이유

2026-10-21 공식 라이브러리 표기 기준이다. 다운로드 크기는 VRAM 요구량과 같지 않다. 실제 메모리에는 문맥 KV 캐시와 연산 버퍼가 더해진다.

| 모델 | 다운로드 | 이번 단계의 판단 |
| --- | --- | --- |
| `exaone3.5:7.8b-instruct-q4_K_M` | 약 4.77GB | 현재 Ollama 기본 모델. Q4_K_M, 실제 전체 GPU 배치 약 5.73GB. 품질 한계는 011 보고 참조 |
| `qwen3:4b-instruct-2507-q4_K_M` | 약 2.5GB | 이전 Ollama 기본 모델, 보존/명시 선택 가능. 4B Q4 모델로 8GB GPU에 메모리 여유를 두며 비사고형 대화·구조화 출력 검증에 사용 |
| `qwen3:8b` | 약 5.2GB | 더 큰 모델과 대사 품질을 비교할 후보. 이번에는 다운로드·추론 검증하지 않음 |
| `gemma3:4b` | 약 3.4GB | 다국어 대화 비교 후보. 이미지 기능은 사용하지 않으며 이번에는 다운로드·검증하지 않음 |
| `qwen3:4b` | 약 2.5GB | 최초 시험 모델. 현재 태그는 thinking 가중치를 가리키며 이 프롬프트의 구조화 출력에서 인사를 반복해 기본 후보에서 제외 |

크기·태그 근거: [Qwen3 태그 목록](https://ollama.com/library/qwen3/tags), [Qwen3 8B](https://ollama.com/library/qwen3:8b), [Gemma3 4B](https://ollama.com/library/gemma3:4b). 비사고형 모델 성격은 [Qwen 공식 모델 카드](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)를 참고했다. 일반적인 모델 비교 성능이 이 게임의 한국어 캐릭터 품질을 보장하지는 않는다.

## 설정

[app/settings.py](../app/settings.py)가 앱 생성 시 읽는다. [.env.example](../.env.example)은 예시이며 `.env` 파일 자동 로딩은 구현하지 않았다. 셸에서 export하거나 실행 명령 앞에 지정한다.

| 환경변수 | 기본값 | 의미 |
| --- | --- | --- |
| `CHARACTER_CHAT_DEV` | `false` | 요청별 판정·모델 입출력을 API/화면에 표시. 저장하지 않음 |
| `CHARACTER_CHAT_PROVIDER` | `mock` | `mock` 또는 `ollama`. 오타는 시작 시 오류 |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama 서버 주소. 인증정보를 URL에 넣지 않음 |
| `OLLAMA_MODEL` | `exaone3.5:7.8b-instruct-q4_K_M` | 설치된 로컬 모델명. 없으면 오류이며 자동 다운로드 안 함 |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | HTTP 연결·읽기 등 단계의 대기 제한. 전체 호출의 엄격한 wall-clock 마감은 아님 |
| `OLLAMA_NUM_CTX` | `8192` | 문맥 크기 |
| `OLLAMA_NUM_PREDICT` | `512` | 생성 토큰 상한 |

체크포인트는 게임 설정·대화·상태를 복원한다. 생성기·모델 선택은 현재 서버 설정을 따르고 체크포인트에 별도로 고정하지 않는다. 과거 대사는 저장된 그대로 복원되며, 이후 다른 모델로 생성한 새 문장의 동일성은 보장하지 않는다.

## 호출과 저장 검증

free 입력은 먼저 `interpret()`에서 의도·대상·원문 근거만 제안하고 기존 서버가 판정한다. `build_context()`는 선택 분기의 판정 후 예상 상태·확정 사건·질문 근거를 준비한다. `character_instructions()`는 그 분기의 NPC용 설정 항목만 전달하며 작가·플레이어 목적은 입력에 넣지 않는다.

`confirmed_history()`는 사용자 발언과 서버 사건을 구분하고, `conversational_history()`는 검토된 잡담 맥락, `reading_context()`는 실제 열람 사건의 본문을 제공한다. 일반 잡담/공간 질문에는 캐릭터 지식·관찰·관계를, 기록 질문과 행동 결과에는 해당 근거를 전달한다. 원본 대사는 저장·복원하며 복원 링크·debug·다른 분기는 모델 입력에 넣지 않는다.

`POST /api/chat`은 `stream=false`, `think=false`와 단계별 JSON Schema를 사용한다. 초안 temperature=0.6, 의도·검토=0이다. Proposal의 표정·수치·결과 필드는 서버 판정 `const`를 더하고 반환값도 다시 검증한다. 같은 모델의 기존 review 호출로 대사와 사실을 비교한다. 호출 횟수를 늘리는 새 평가기는 추가하지 않았다. [공식 구조화 출력](https://docs.ollama.com/capabilities/structured-outputs), [chat API](https://docs.ollama.com/api/chat)

- 연결·타임아웃·HTTP 오류, 과도한 크기, 잘못된 외부 JSON·내부 JSON, 중복 필드, 미완성·토큰 상한 종료, 빈 대사, 잘못된 제안은 502로 거부한다.
- 유사도에 따른 거부·자동 재생성은 없다. 대사 초안은 한 번 생성하며 반복 자체를 오류로 만들지 않는다. 기존 별도 review()에서 사실 일치를 검토하고 모순 판정/서버 마무리 대상은 서버 문장으로 대체한다. `generation.attempts`는 1이다. 연결·형식·상태 오류의 자동 재시도나 mock 대체도 없다.
- UTF-8 바이트와 역할 오버헤드를 이용한 보수적 문맥 예산 검사로 너무 긴 입력을 전송 전에 거부한다. 정확한 토큰 계산기는 아니며 과거 대화를 몰래 잘라 넣지 않는다. 긴 대화 요약·토큰 최적화는 미구현이다.
- 모델 호출은 DB 쓰기 트랜잭션 밖에서 한다. 성공한 제안을 `Proposal`·`apply_turn()`으로 다시 검사하고 revision이 유효할 때만 턴과 자동 체크포인트를 함께 저장한다.
- 반환되는 `generation`은 요청별 모델명·소요 시간·Ollama 측 통계다. 서버의 공유 마지막 응답 변수는 사용하지 않으며 진단 정보는 게임 스냅샷에 저장하지 않는다.
- free는 의도·대사·검토 3회, direct는 대사·검토 2회다. 검토 모델도 오판 가능하므로 상태 검증 통과와 대사의 사실성·품질은 구분한다. 새 게임 archive-3.0의 NPC용 설정은 character_instructions()에서 선택하며 작가·플레이어용 문서는 읽지 않는다.

## 검증 실행

LLM 없이 오류·상태 검증:

```bash
.venv/bin/python -m pytest -q
```

실제 모델 검증 (Ollama 서버와 모델이 준비된 상태에서):

```bash
.venv/bin/python -m scripts.verify_ollama
```

별도 임시 DB에서 실제 모델로 공개 목록·선택·열람, 열람 전 회귀, 신분증 주장·봉인 허가 요구·공개 경로 전환, 강제 접근 경고·종료의 11사례를 검증한다. 상태 검증은 자동 실행하지만 원본 대사의 의미·질문 응답성은 보고서로 별도 수동 검토한다. 실패 결과도 임시 보고서에 남긴다. 플레이 중 DB는 수정하지 않는다. 결과는 Git 제외 파일 `.runtime/ollama-validation.json`에 기록한다.

추가 회상 질문 검증:

```bash
.venv/bin/python -m scripts.verify_record_recall
```

선택식 준비는 mock, 3개 기록별 선택·열람·회귀 질문과 바꿔 묻기·다른 기록 선택 후 회상은 실제 모델로 확인한다. 결과는 `.runtime/008-record-recall.json`, 별도 수동 품질 검토는 [008 보고](reports/008-record-recall.md)다.

GPU와 모델 상태:

```bash
.runtime/ollama/bin/ollama ps
curl -sS http://127.0.0.1:11434/api/ps
nvidia-smi
```

`ollama ps`의 `100% GPU`는 모델 전체가 GPU 메모리에 올라갔다는 의미이며 순간 GPU 연산 사용률 100%라는 의미는 아니다. [공식 GPU 배치 확인 안내](https://docs.ollama.com/faq#how-can-i-tell-if-my-model-was-loaded-onto-the-gpu)

## 004 단계의 최초 연결 검증 보고 (과거 측정)

측정일: 2026-10-21 (Asia/Seoul). hostname `lee`, WSL2 커널 `6.18.54.1-microsoft-standard-WSL2`, RTX 3070 Ti 8GB. 제한된 실행에서는 NVML 차단이 있었지만 제한 밖의 읽기 전용 진단과 실제 추론에서 GPU 접근을 확인했다. WSL에서 관측한 RAM은 약 15.6GiB로 장비 RAM 32GB 전체와는 다르며, 이 설정은 변경하지 않았다.

- Ollama **0.40.6**, 실제 모델 **`qwen3:4b-instruct-2507-q4_K_M`**, Q4_K_M, 모델 digest 접두사 `0edcdef34593`.
- `ollama ps`: **100% GPU**, context 8192. `/api/ps`: size와 size_vram 모두 **3,877,571,133바이트** (약 3.9GB).
- `nvidia-smi`: 최종 모델 관측 시 전체 GPU **5,287MiB / 8,192MiB** 사용. 설치 전에는 1,434MiB였다. 전체 GPU 사용량에는 다른 작업도 포함한다.
- 테스트는 임시 DB에서 진행했고 플레이 DB는 사용하지 않았다. 회귀 뒤 설정·기억·사건·요약의 동등성 및 미래 입력 제외를 확인했다.
- 검증용 Ollama 서버는 측정 후 종료했다. 실제 연결 실패 테스트에서 **502, 상태·대화·revision 유지, 자동 체크포인트 없음**을 확인했다. 사용하려면 위 서버 실행 명령부터 시작한다.

| 실제 입력 사례 | 응답 시간 | 상태 검증 |
| --- | ---: | --- |

| 인사 | 3.92초 | 통과 |
| 설정 무시·성공 주장 | 0.71초 | 통과 |
| 열람 거절 | 3.70초 | 통과 |
| 강제 접근 경고 | 0.85초 | 통과 |
| 재시도 종료 | 0.81초 | 통과 |
| 회귀 후 새 입력 | 2.20초 | 통과 |

6회 측정 범위는 **0.71–3.92초**, 중앙값 **1.52초**. 최종 instruct 모델의 첫 호출은 3.92초였으며, 이후 호출 범위는 0.71–3.70초였다. 이는 짧은 시험 입력 6개의 결과로 일반적인 응답 시간이나 cold-start 상한을 보장하지 않는다.

최초 시험 `qwen3:4b`는 모델 최초 로딩 포함 43.35초, 로딩 이후 0.65–0.83초였지만 인사를 반복하여 대사 품질상 채택하지 않았다. 이 값은 최종 instruct 모델의 측정값과 구분한다. 프롬프트에 장면별 지시를 추가한 뒤에도 thinking 모델의 반복 문제가 남아 명시적 instruct 태그로 전환했다. 별도 비사고 지시 독립 시험에서는 경고 대사를 만들었지만 기본 모델로는 선택하지 않았다.

### 실제 대사 표본과 남은 품질 문제

- **설정 무시·성공 주장**: 이전 규칙을 무시하거나 기록을 가져간다는 주장은 확인되지 않았습니다. 신분과 행동 성공은 사용자의 주장에 의해 확정되지 않습니다.
- **강제 접근 경고**: 강제로 기록에 접근하려는 시도는 금지되어 있습니다. 즉시 멈추고, 허가를 받기 전에는 어떠한 행동도 하지 마십시오.
- **재시도 종료**: 강제 접근이 반복됐습니다. 기록은 봉인 상태이며, 면담은 지금 종료됩니다. 퇴장해 주세요.

최종 모델은 요청 맥락에 따라 다른 대사를 생성했고, 시험 표본에서 주장을 세계 사실로 확정하거나 봉인 해제를 허용하지 않았다. 다만 열람 거절 대사의 “열람 허이나” 같은 오타가 있고, 첫 경고 대사에서 재시도 시 종료된다는 예고가 생략됐다. 상태·종료 적용은 서버 규칙대로 정확했지만 문장 품질과 의미적 일관성 전체를 검증했다고 볼 수는 없다.

### 자동 검증과 확인 한계

- **Python 테스트 55개 통과**: mock 유지·설정 선택, Ollama HTTP 모의 성공·오류·타임아웃·잘못된 JSON·중복 필드·잘못된 수치·미완성·크기 제한·문맥 제한에서의 원자성, 복원 뒤 실제 HTTP 요청 메시지의 미래 정보 제외, 기존 게임·회귀 테스트.
- 실제 모델 6사례 상태 검증과 실제 서버 종료 후 연결 실패 검증도 통과했다.
- `node tests/test_ui.cjs`, JavaScript 구문 검사, `bash -n scripts/serve_ollama.sh` 통과. 실제 사용자 브라우저·VS Code 화면 렌더링은 직접 확인하지 못했다.
- Starlette가 httpx 대신 httpx2 사용을 권하는 경고 1개는 기존대로 남아 있다.
- 다른 두 후보의 VRAM·지연·대화 품질은 실측하지 않았다. 긴 플레이, 실제 토큰 예산과 요약 최적화, 모델별 대사 평가를 더 진행해야 한다.


## 005 단계의 인사 반복 재현과 보완 (과거 기록)

이 절은 당시 결과를 보존한다. **006에서 아래 유사도 차단·재생성 정책을 제거했다.** 현재 정책과 원인 조사 결과는 [006 진단 기록](dialogue-diagnosis.md)을 참고한다.

사용자 로그와 실행 중 health에서 올바른 instruct 모델을 확인했지만, `안녕 → 안녕` 입력에서 첫 인사 전문을 그대로 반복하는 문제를 재현했다. 따라서 004에서 긴 인사·상황 입력 6개를 확인한 것만으로 모든 반복 문제가 해결됐다고 볼 수 없었다.

첨부 로그는 GPU 37/37 계층 적재, 문맥 8192, `truncated=0`, 실제 200 응답을 보여 준다. `</s>` 타입 경고는 보정 후 실행이 계속됐으며 이것을 반복 원인으로 확정하지 않았다. 템플릿 초기화의 thinking 표기도 개별 요청의 사고 모드가 실제 켜졌다는 증거로 간주하지 않았다. 이번에는 모델 설치·시스템 설정을 변경하지 않았다.

### 005 당시 구현

- 지시를 간소화하고, 사용자 발언을 복잡한 JSON 과제로 감싸는 대신 자연어와 표준 대화 역할을 유지한다. 상태 판정은 별도 system 데이터와 JSON Schema로 통제한다.
- 같은 발언이 연속된 잡담이면 이미 응답한 상황을 인지하도록 장면 지시를 추가한다. 업무 질문에는 캐릭터 본인의 입장에서 답하도록 한다.
- 기본 temperature는 0.6. 직전 대사와 공백 제거 후 같거나, 두 문자열이 각각 24자 이상이고 `SequenceMatcher` 유사도 0.88 이상이면 한 번만 재생성한다. 보완 system 지시를 현재 입력 앞에 넣고 temperature=0.8을 사용한다.
- 두 번째 결과도 모든 형식·상태 검증을 통과해야 한다. 재반복·타임아웃·잘못된 제안은 502이며 대화·revision·자동 체크포인트를 저장하지 않는다. 첫 번째 거부된 대사는 다음 대화 기억에 들어가지 않는다.
- `generation.attempts`는 1 또는 2다. `elapsed_ms`는 두 호출을 포함한 전체 생성 시간, Ollama의 토큰·duration 통계는 최종 호출 기준이다. 재생성 지시 공간도 문맥 예산에 미리 포함한다.

### 검증 범위와 남은 문제

Python 테스트 60개가 통과했다. 새 검증은 정확·유사 인사 반복 후 재생성 성공 시 1턴만 저장, 재반복·두 번째 호출 타임아웃·잘못된 상태 제안 시 무저장을 포함한다. 실제 모델 검증 스크립트도 `안녕` 2회와 업무 질문을 포함하는 8사례로 확장했다. 상세 결과는 [변경 기록](changes.md)의 005에 남긴다.

문자열 유사도 검사는 의미 전체를 평가하지 않는다. 표현만 조금 다른 반복이 통과하거나, 정당한 반복 거절이 차단될 수 있다. 여전히 열람 목적을 묻는 표현이 잦고 한국어가 어색할 때가 있다. 따라서 반복 저장 방지와 자연스러운 캐릭터 대화 품질은 구분한다. 004의 수치는 과거 측정으로 보존하며 현재 성능 보장으로 쓰지 않는다.

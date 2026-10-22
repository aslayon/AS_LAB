# 기록 보관소 · 캐릭터 채팅 프로토타입

보관인 **서린**과 자유롭게 대화하며 기록을 탐색하는 로컬 LLM 게임이다. 최종 목표는 **계몽의 서 봉인 해제와 본문 확인**이다.

LLM은 사용자 의도를 해석하고 대사를 생성한다. **사건·관계·열람 허가·종료는 서버가 판정**하므로, 사용자 주장이나 모델의 허가 선언만으로 게임 상태가 바뀌지 않는다.

현재 버전을 학습용 프로토타입의 최종 기준으로 보존한다. 설계 과정과 실험 결과는 [최종 보고서](docs/final-report.md)에 정리했다.

## 주요 기능

- 자유 입력으로 공개 기록 목록 요청·선택·열람
- 신뢰·경계 변화와 기밀 제목의 출처 확인
- 관계 조건에 따른 확률 판정과 고정 결말
- 선택한 답변 시점으로 회귀하고 새 분기 생성
- 성공·실패 판정 보존과 Markdown/JSON 내보내기
- 모델 없이 실행하는 mock 모드

모델 학습·파인튜닝, 유료 API, 로그인·결제, 이미지 생성, 벡터 DB는 사용하지 않는다.

## 기술 구성

| 항목 | 구성 |
| --- | --- |
| 서버·저장 | Python / FastAPI / SQLite |
| 화면 | HTML / CSS / JavaScript — 별도 프런트 빌드 불필요 |
| 실행 환경 | WSL2 + VS Code, Python 3.14.4, 프로젝트 전용 `.venv` |
| 로컬 모델 | Ollama 0.40.6 / `exaone3.5:7.8b-instruct-q4_K_M` |
| 장비 | Ryzen 5700X / RAM 32GB / RTX 3070 Ti 8GB |
| 모델 설정 | 문맥 8192 / 생성 상한 512 / 제한 시간 120초 |
| 호출 구성 | 자유 입력: 의도 해석 → 초안 → 검토, 총 3회 |

직접 행동 지정은 의도 해석을 생략해 2회 호출한다. 의도·검토 temperature는 0, 초안은 0.6이다. WSL 가용 RAM은 측정 당시 약 15.6GiB였다.

의존성 버전은 [requirements.lock](requirements.lock), 환경 상세는 [Ollama 안내](docs/ollama.md)를 참고한다.

## 설치

```bash
cd ~/projects/AS_LAB/character-chat
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
```

시스템 Python은 변경하지 않는다. 다른 환경으로 옮겼다면 `.venv`를 복사하지 말고 새로 만든다.

<details>
<summary>ensurepip 오류로 가상환경 생성이 실패할 때</summary>

다음은 PyPA 설치 스크립트를 내려받아 프로젝트 가상환경에만 pip를 설치하는 방법이다.

```bash
cd ~/projects/AS_LAB/character-chat
python3 -m venv --without-pip .venv
curl -fL https://bootstrap.pypa.io/get-pip.py -o /tmp/character-chat-get-pip.py
.venv/bin/python /tmp/character-chat-get-pip.py
.venv/bin/python -m pip install -r requirements.lock
```

각 명령이 성공한 것을 확인한 뒤 다음 명령을 실행한다.

</details>

## 실행

### mock 모드

Ollama와 GPU 없이 화면·상태·회귀 기능을 확인한다. 정해진 예문을 처리하는 고정 응답 방식이므로 일반 자연어 이해를 평가하는 용도로는 사용하지 않는다.

```bash
cd ~/projects/AS_LAB/character-chat
CHARACTER_CHAT_PROVIDER=mock \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Ollama 모드

Ollama 본체가 없다면 먼저 [설치 안내](docs/ollama.md)를 따른다. 터미널 하나에서 Ollama 서버를 실행한다.

```bash
cd ~/projects/AS_LAB/character-chat
bash scripts/serve_ollama.sh
```

모델이 없다면 다른 터미널에서 다운로드한다.

```bash
cd ~/projects/AS_LAB/character-chat
OLLAMA_HOST=127.0.0.1:11434 \
.runtime/ollama/bin/ollama pull exaone3.5:7.8b-instruct-q4_K_M
```

다운로드가 끝나면 게임 서버를 실행한다.

```bash
CHARACTER_CHAT_PROVIDER=ollama \
OLLAMA_MODEL=exaone3.5:7.8b-instruct-q4_K_M \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- 게임: <http://localhost:8000>
- API 명세: <http://localhost:8000/docs>
- 종료: 각 터미널에서 `Ctrl+C`
- WSL 접속이 안 될 때: VS Code의 8000 포트 전달 확인

`.env`는 자동으로 읽지 않는다. `.env.example`은 안내용이며, 이전에 export한 환경변수가 기본값보다 우선한다. 기본 DB는 `data/game.sqlite3`다. 다른 DB를 쓰려면 실행 명령 앞에 `CHARACTER_CHAT_DB=data/my-game.sqlite3`를 추가한다.

## 기본 플레이

1. **새 게임**을 만든다.
2. “공개 기록 목록을 보여주세요.”라고 입력한다.
3. “방문 기록을 선택할게요.” → “선택한 기록을 읽어주세요.” 순으로 진행한다.
4. 반출입 장부와 보관 분류 안내도 선택하고 읽는다.
5. “계몽의 서라는 이름을 들었습니다.”라고 말하고 출처 질문에 답한다.
6. “계몽의 서를 읽고 싶습니다. 열람을 허용해 주세요.”라고 요청한다.

서로 다른 공개 기록의 첫 열람마다 **신뢰 +10 / 경계 −5**, 최대 3회 적용된다. 기밀 제목을 처음 언급하면 경계가 10 증가한다. 인사·칭찬·재열람 반복에는 보상이 없다. 출처 답변은 미검증 주장으로 취급하며, 질문 종료가 사실 확인을 의미하지 않는다.

| 열람 판정 | 기본 규칙 |
| --- | --- |
| 자격 | 신뢰 ≥50, 경계 ≤30, 공개 기록 2개 이상 열람 |
| 추가 조건 | 강제 접근 없음, 기밀 제목 인지, 출처 질문 종료 |
| 성공 확률 | `clamp(0.10 + 0.01×trust − 0.005×guard, 0.05, 0.85)` |
| 판정 횟수 | 분기당 1회. 자격 미달 요청은 소모하지 않음 |
| 성공 | 고정 본문 공개 후 분기 종료 |
| 실패 | 대화는 계속 가능하나 같은 분기에서 재추첨 불가 |

세 기록 열람과 제목 언급 뒤 추가 변화가 없다면 신뢰 60 / 경계 15, 성공 확률은 **62.5%**다. 강제 접근은 경고·반복 종료로 이어지며 성공 경로가 아니다.

자연어 의도는 오분류될 수 있으므로 화면의 서버 판정도 확인한다. 상세 내용은 [열람 규칙](docs/access-rules.md), [실제 성공 기록](docs/examples/015-success.md)을 참고한다.

## 설정 변경

| 파일 | 수정 내용 |
| --- | --- |
| [config/world.json](config/world.json) | 배경·성격·판단 기준·공개 기록·첫 대사 |
| [config/relationship_rules.json](config/relationship_rules.json) | 관계 증감·반복 한도·열람 자격·확률 |
| [config/ending.json](config/ending.json) | 성공 시 공개할 고정 결말 |

변경 후 **서버 재시작 → 새 게임 생성**이 필요하다. 기존 분기는 당시 설정의 실제 값과 버전을 보존한다. 모델 선택은 서버 실행 설정을 따른다.

`world.json`은 모델에 전달될 수 있으므로 비밀 본문을 넣지 않는다. 결말은 `ending.json`, 서버 기밀 정의는 `app/confidential.py`, 플레이어 전용 목적은 `docs/scenario.md`로 분리돼 있다. 항목별 설명은 [설정 편집 안내](docs/configuration-guide.md)에 있다.

## 회귀와 결과 보존

**↶ 여기로 회귀**를 누르면 선택한 사용자 입력과 서린의 답변까지 유지한 새 분기가 만들어진다. 대화·관계·사건·설정이 함께 복원되며 원본 분기는 남는다. 판정 전으로 회귀하면 새 시도가 가능하고, 판정 후로 회귀하면 사용한 판정과 종료 상태도 복원된다.

성공 기록은 화면에서 Markdown/JSON으로 다운로드할 수 있다. 자동 저장 위치는 `data/exports/<기록ID>-<새UUID>/`이며 실패·보류 판정도 별도 실험 기록에 남는다.

- **파일 저장 실패:** DB 결과는 유지된다. 같은 DB로 분기를 불러 다운로드하거나 다시 내보낸다.
- **추첨 예약 뒤 모델·저장 오류:** 화면에서 같은 요청을 재전송한다. 저장된 판정값을 재사용한다.
- **DB 삭제:** 결과 복구에 필요한 원본도 사라지므로 주의한다.

복구 API와 세부 조건은 [내보내기·복구 안내](docs/access-rules.md)에 있다. 실행 DB, 모델, 런타임 로그, 자동 내보내기 파일, 키 파일은 Git에서 제외한다.

## 검증 범위와 한계

최종 구현 단계의 기록은 **Python 테스트 253개·JavaScript DOM 검사 3종 통과**, 실제 모델 3분기의 결말 도달이다. 자동 기능 검사와 실제 대사 품질은 별개이며, 이 문서 정리에서는 테스트를 다시 실행하지 않았다.

```bash
.venv/bin/python -m pytest -q
```

남은 문제는 의도·출처 오분류, 어색하거나 반복되는 대사, 설정 밖 사실 생성, 검토 모델의 오류 누락이다. 긴 대화는 문맥 예산 검사에서 중단될 수 있다. 실제 브라우저 자동 검증·저장량 최적화·확률의 통계적 검증은 완료하지 않았다.

공개 기록 보상은 진행 경로 검증용 규칙이다. **정서적 설득에 따른 관계 변화는 구현하지 않았다.** 자세한 검증 조건과 실패 사례는 [최종 보고서](docs/final-report.md)에 정리했다.

## 관련 문서

| 문서 | 내용 |
| --- | --- |
| [최종 보고서](docs/final-report.md) | 설계 과정·모델 비교·검증 결과·한계 |
| [현재 구조](docs/architecture.md) | 처리 흐름과 Mermaid 구조도 |
| [설정 편집 안내](docs/configuration-guide.md) | 수정 항목과 적용 방법 |
| [관계 규칙](docs/relationship-rules.md) / [열람·복구 규칙](docs/access-rules.md) | 수치·자격·확률·오류 처리 |
| [Ollama 안내](docs/ollama.md) | 설치와 실행 환경 |
| [변경 이력](docs/changes.md) / [최종 스냅샷](docs/architecture-history/015-access-ending.md) | 단계별 변경과 검증 근거 |

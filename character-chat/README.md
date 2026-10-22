# 기록 보관소 · 캐릭터 채팅 프로토타입

자유로운 사용자 입력을 보관인 **서린**의 대화로 연결하고, 사건·관계·종료 상태는 서버가 관리하는 학습용 프로토타입이다. 최종 목표는 **계몽의 서 봉인 해제 및 내용 확인**이다. 현재 구현을 최종 기준선으로 보존하며, 대사 품질이 완성됐다는 뜻은 아니다. [최종 보고서](docs/final-report.md)에 설계 과정·실험 결과·남은 문제를 정리했다.

구현 범위는 자유 입력의 의도 해석, 공개 기록 목록·선택·열람, 신뢰/경계 변화, 기밀 제목·출처 질문, 서버 확률 판정, 고정 결말, 분기 회귀, Markdown/JSON 자동 저장·다운로드다. 모델의 허가 선언만으로 사건이 완료되지 않는다. 기본 mock은 고정 대역이며 일반 자연어 이해를 제공하지 않는다.

## 환경과 의존성

| 항목 | 현재 기준과 근거 |
| --- | --- |
| 앱 | Python FastAPI + SQLite + HTML/CSS/JavaScript. 프런트 빌드·Node 실행 불필요 |
| 검증 환경 | Python 3.14.4, WSL2 + VS Code. 시스템 Python 대신 프로젝트 `.venv` 사용 ([환경 기록](docs/ollama.md)) |
| 직접 의존성 | FastAPI 0.156.0, Uvicorn 0.54.0, httpx 0.28.1, pytest 9.1.1 ([requirements.txt](requirements.txt)) |
| 전체 고정 목록 | Pydantic 2.14.1·Starlette 1.9.0 등을 포함한 [requirements.lock](requirements.lock) |
| 기본 실행 | `MockProvider`, 모델 없음. 실제 로컬 모델은 Ollama 모드에서 선택 |
| 실제 사용 모델 | Ollama 0.40.6 / `exaone3.5:7.8b-instruct-q4_K_M`, Q4_K_M ([011](docs/reports/011-exaone.md), [015](docs/reports/015-access.md)) |
| 기본 모델 설정 | 문맥 8192, 생성 상한 512, 제한 시간 120초. 의도·검토 temperature 0, 초안 0.6 ([settings.py](app/settings.py), [생성기](app/ollama_provider.py)) |
| 관측 장비 | Ryzen 5700X·RAM 32GB·RTX 3070 Ti 8GB. WSL 가용 RAM은 당시 약 15.6GiB였으며 호스트 RAM 전체와 다름 ([모델 비교](docs/reports/model-selection.md)) |

모델 학습·파인튜닝, 유료 API, 로그인·결제, 이미지 생성, 벡터 DB는 포함하지 않는다. 일반 자유 입력 한 턴은 의도→초안→검토의 모델 호출 3회다. 직접 행동은 2회이며, 보류 판정 재개는 저장된 의도를 재사용한다.

## 설치와 실행

이미 이 작업 공간의 `.venv`가 있으면 설치 없이 실행한다. 다른 환경에서는 Python의 venv/pip를 사용할 수 있어야 한다. `.venv`와 `.runtime`은 Git에 포함되지 않으며 복사한 가상환경 대신 새로 만든다.

```bash
cd ~/projects/AS_LAB/character-chat
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
```

당시 도구 환경에는 `ensurepip`가 없어 아래 방법으로 프로젝트 가상환경에만 pip를 설치했다. 같은 오류가 있을 때 사용하는 네트워크 설치 절차다.

```bash
python3 -m venv --without-pip .venv
curl -fL https://bootstrap.pypa.io/get-pip.py -o /tmp/character-chat-get-pip.py
.venv/bin/python /tmp/character-chat-get-pip.py
.venv/bin/python -m pip install -r requirements.lock
```

**mock 실행:** Ollama와 GPU 없이 동작한다.

```bash
cd ~/projects/AS_LAB/character-chat
CHARACTER_CHAT_PROVIDER=mock \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Ollama 실행:** 터미널 하나에서 프로젝트 내부 Ollama 서버를 켠다.

```bash
cd ~/projects/AS_LAB/character-chat
bash scripts/serve_ollama.sh
```

다른 터미널에서 게임 서버를 켠다.

```bash
cd ~/projects/AS_LAB/character-chat
CHARACTER_CHAT_PROVIDER=ollama \
OLLAMA_MODEL=exaone3.5:7.8b-instruct-q4_K_M \
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

브라우저는 <http://localhost:8000>, API 명세는 <http://localhost:8000/docs>다. WSL 연결이 안 되면 VS Code의 8000 포트 전달을 확인한다. 서버는 Ctrl+C로 종료한다. Ollama 본체·가중치가 없다면 [설치 위치·절차](docs/ollama.md)를 따른다. 기본 모델 다운로드는 Ollama 서버가 켜진 다른 터미널에서 다음과 같이 실행한다.

```bash
OLLAMA_HOST=127.0.0.1:11434 \
.runtime/ollama/bin/ollama pull exaone3.5:7.8b-instruct-q4_K_M
```

`.env.example`은 안내용이며 **`.env` 자동 로딩은 없다**. 이전에 export한 환경변수가 기본값보다 우선한다. `GET /api/health`는 선택된 생성기·모델 설정만 표시하며 실제 추론·GPU 성공을 보증하지 않는다. 기본 DB는 `data/game.sqlite3`, 다른 DB는 서버 실행 명령 앞에 `CHARACTER_CHAT_DB=data/my-game.sqlite3`를 추가한다.

## 새 게임부터 열람 시도까지

1. 화면에서 **새 게임**을 만들고 기본 자유 입력으로 대화한다. mock은 정해진 예문만 처리하므로 일반 문장의 이해력을 평가할 때는 Ollama를 사용한다.
2. “공개 기록 목록을 보여주세요.” → “방문 기록을 선택할게요.” → “선택한 기록을 읽어주세요.” 순으로 진행한다. 서버 결과 카드와 고정 본문을 확인한다.
3. 반출입 장부·보관 분류 안내도 각각 선택하고 읽는다. 서로 다른 기록의 첫 열람만 신뢰 +10/경계 −5, 기본 최대 3회다. 인사·칭찬·재열람 반복에는 보상이 없다.
4. “계몽의 서라는 이름을 들었습니다.”처럼 제목을 언급하고 출처 질문에 답한다. 사용자 설명은 미검증 주장이다. 출처 질문 종료가 진실 확인을 뜻하지 않는다.
5. 실제 열람을 요청한다. 예: “계몽의 서를 읽고 싶습니다. 열람을 허용해 주세요.” 의도 오분류 가능성이 있으므로 서버 판정도 확인한다.

기본 자격은 **신뢰 ≥50, 경계 ≤30, 공개 기록 2개 이상, 강제 접근 없음, 제목 인지, 출처 질문 종료**다. 자격 미달은 기회를 소모하지 않는다. 확률은 `clamp(0.10 + 0.01×trust − 0.005×guard, 0.05, 0.85)`이고 분기당 한 번이다. 세 기록 열람과 제목 인지 후 추가 감점이 없으면 60/15, 성공 확률 62.5%다. 실패 뒤에는 대화를 이어갈 수 있지만 같은 분기에서 재추첨하지 않는다. 강제 접근은 경고·반복 종료이며 성공 경로가 아니다. 자세한 [규칙·계산·상태 전이](docs/access-rules.md)와 [실제 성공 원문](docs/examples/015-success.md)을 참고한다.

## 설정 편집과 적용

| 수정 파일 | 수정 대상 |
| --- | --- |
| [config/world.json](config/world.json) | 배경·성격·판단 기준·공개 기록·첫 대사 (`archive-5.0`) |
| [config/relationship_rules.json](config/relationship_rules.json) | 초기 신뢰/경계·증감·반복 한도·임계치·열람 자격/확률 (`relationship-2.0`) |
| [config/ending.json](config/ending.json) | 열람 성공 시 고정 결말 제목·본문 (`enlightenment-ending-1`) |

편집 후 게임 서버를 Ctrl+C로 종료하고 위 mock/Ollama 명령으로 **재시작 → 새 게임 생성**한다. JSON 변경만으로 실행 중 설정이 갱신되지는 않는다. 시작할 때 형식과 필수 항목을 검증하며 오류에 파일 경로와 항목이 표시된다. 기존 분기·체크포인트는 당시 실제 값과 버전을 보존하므로 같은 버전 문자열의 내용을 바꿔도 옛 게임에 적용되지 않는다. 모델 선택 자체는 서버 실행 설정을 따른다.

[편집 안내](docs/configuration-guide.md)에 항목별 예시, 문구와 코드 ID의 구분, trust/guard의 실제 사용 범위가 있다. `world.json`은 모델에 전달될 수 있는 일반 설정이다. 비밀 본문은 `ending.json`, 서버 기밀 정의는 [confidential.py](app/confidential.py), 플레이어 전용 목적은 [scenario.md](docs/scenario.md)에 분리돼 있다. 비밀을 일반 배경 문자열에 넣으면 자동으로 숨겨 주지 않는다.

## 회귀·결과 다운로드·복구

- 발언 옆 **↶ 여기로 회귀**는 선택한 사용자 입력과 서린의 답변까지 남긴 새 분기를 만든다. 원본 분기는 보존된다. 판정 전으로 회귀하면 새 분기의 별도 시도이며, 판정 후로 회귀하면 사용 완료·종료도 복원된다.
- 성공하면 고정 결말 본문을 표시하고 분기를 종료한다. 화면에서 Markdown/JSON 다운로드와 실제 저장 위치를 확인한다. 기본 자동 저장은 `data/exports/<기록ID>-<새UUID>/report.md`, `report.json`이다. 실패·보류 판정도 별도 실험 기록으로 남는다.
- 파일 쓰기에 실패해도 DB의 게임 결과·판정값은 남는다. 같은 DB로 서버를 켜고 분기를 불러 **다운로드**하거나 **다시 내보내기**로 새 복사본을 만든다. DB 자체를 삭제하면 이 복구 근거도 사라진다.
- API는 `POST /api/branches/{branch_id}/exports/retry`, `GET /api/exports/{export_id}/markdown` 또는 `/json`이다. 다운로드는 파일 대신 DB의 저장된 보고서로 생성한다.
- 추첨 예약 뒤 모델/턴 저장 오류가 났으면 화면의 같은 요청 재전송을 사용한다. 저장된 판정값을 재사용하며 새 난수를 뽑지 않는다. 세부 조건은 [복구 안내](docs/access-rules.md)에 있다.

실행 DB·WAL/SHM, `.runtime/` 전체 원본 로그, `data/exports/`, `.env`·키 파일은 Git 제외다. 기존에 선별 보존한 `docs/reports/`의 실험·실패 증거는 유지하며, 최종 대표 사례는 개인정보·비밀키를 점검한 Markdown 사본 하나만 `docs/examples/`에 보존했다.

## 알려진 문제와 미구현 사항

한국어 어색함·불필요한 질문 반복, 설정 밖 사실·절차 생성, 의도·출처·접근 방식 오분류와 검토 모델의 누락이 남는다. 서버 상태의 일관성이 대사 품질을 보장하지 않는다. 긴 대화는 보수적인 문맥 예산에 걸려 502로 중단될 수 있으며 대화/스냅샷/보고서 저장량 최적화도 미구현이다. 실제 브라우저·Mermaid 렌더링은 미확인이고, 기존 Starlette/httpx 경고가 남는다.

접근 방식 진단은 수치와 연결하지 않았다. 공개 기록 보상은 성공 경로 검증용 게임 규칙이며 정서적 설득의 효과를 검증한 시스템이 아니다. 신분증·신원·권한·거래 검증, 잠입·아이템 시스템도 미구현이다. 배경 상세도·관계 설정 변경의 체계적 효과 비교와 확률의 통계적 검증은 수행하지 않았다. [실패 사례](docs/failure-cases/014-approaches.md)와 [최종 한계](docs/final-report.md#⑧-한계와-배운-점)를 함께 본다.

## 문서와 검증 근거

- [문서 인덱스·가져오기 기준](docs/README.md), [최종 보고서](docs/final-report.md), [대표 성공 기록 원문](docs/examples/015-success.md)
- [현재 구조·Mermaid](docs/architecture.md), [최종 구현 스냅샷 015](docs/architecture-history/015-access-ending.md), [최초 mock 스냅샷](docs/architecture-history/001-mock.md)
- [A/B 비교](docs/reports/dialogue-ab.md), [세 모델 비교](docs/reports/model-selection.md), [EXAONE 채택 검증](docs/reports/011-exaone.md)
- [접근 방식 비교·실패](docs/reports/014-approaches.md), [결말 실험·초기 실패·DB 대조](docs/reports/015-access.md)
- [설정 편집](docs/configuration-guide.md), [관계 규칙](docs/relationship-rules.md), [결말·복구 규칙](docs/access-rules.md), [Ollama 환경](docs/ollama.md)
- [단계별 변경·검증 이력](docs/changes.md), [작업·커밋 규칙](AGENTS.md)

최종 구현 단계에서 Python 253개와 JavaScript DOM 3종 검사를 통과했다는 기록은 [015 변경 기록](docs/changes.md)에 있다. 이번 최종 문서 정리에서는 게임 테스트·모델 실험을 재실행하지 않았다. 필요할 때 기능 테스트 명령은 `.venv/bin/python -m pytest -q`이며, 실제 모델 실험과는 별개다.

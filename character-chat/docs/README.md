# character-chat 문서 안내

- [실행·설정·복구 안내](../README.md)
- [최종 보고서](final-report.md)
- [대표 성공 기록 원문](examples/015-success.md)
- [최종 구조 PNG](diagrams/final-structure.png) / [편집용 SVG](diagrams/final-structure.svg) / [Mermaid 원본](diagrams/final-structure.mmd)
- [현재 구조](architecture.md) / [최종 구현 구조 스냅샷](architecture-history/015-access-ending.md)
- [설정 편집](configuration-guide.md) / [관계 규칙](relationship-rules.md) / [결말·확률·복구](access-rules.md)
- [모델 비교](reports/model-selection.md) / [EXAONE 채택](reports/011-exaone.md)
- [접근 방식 비교](reports/014-approaches.md) / [결말 실험과 실패 기록](reports/015-access.md)
- [단계별 변경 기록](changes.md)

## AS_LAB에 가져온 기준

원본 로컬 프로젝트 `character-chat`의 최종 문서 정리 커밋 `69c1be2d978d5802ac72fe4cef7a5db704ab799f`에서 추적 파일만 가져왔다. 원본 Git 이력은 로컬 원본 저장소에 보존하며 이 하위 폴더에 중첩 `.git`이나 서브모듈을 만들지 않았다.

실행 위치는 AS_LAB을 복제한 경로 아래의 `character-chat/`이다. 예: `cd ~/projects/AS_LAB/character-chat`. 과거 보고서·스냅샷에 등장하는 `~/projects/character-chat`와 `/home/aslayon/projects/character-chat`는 당시 작업 공간의 경로다. 보존 문서는 수정하지 않았으므로 실행 명령의 작업 디렉터리만 현재 체크아웃 경로로 바꿔 사용한다. 이 폴더의 README 실행 예시는 AS_LAB 경로에 맞췄다.

실행 DB·모델 가중치·가상환경·비밀키·`.runtime/` 전체 원본 로그·자동 내보내기는 포함하지 않았다. 기존에 선별해 보존한 실험·실패 증거와 대표 Markdown은 유지했다. `.venv`·Ollama 본체·가중치는 각 환경에 별도로 설치한다. 원본의 미추적 개인 메모도 가져오지 않았다.

가져오기 과정에서 게임 코드·설정·기능은 변경하지 않았고, 모델 실험과 게임 테스트는 다시 실행하지 않았다. 실제 실험의 코드 버전은 해당 원문 메타데이터를 따르며 AS_LAB 가져오기 커밋으로 바꿔 해석하지 않는다.

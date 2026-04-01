# projects 폴더 안내

이 폴더는 `refactored/projects/` 아래의 프로젝트들을 GitHub에 올렸을 때도 한눈에 보기 쉽도록 정리한 구조입니다.

## 포트폴리오용 정리 기준
- 각 프로젝트는 독립된 폴더로 분리합니다.
- 각 프로젝트 폴더에는 최소한 `README.md`와 `docs/README.md`를 둡니다.
- 코드 파일은 가능하면 `src/` 또는 `code/` 같은 하위 폴더로 정리합니다.
- 애매한 요약본, 보조 문서, 정리용 파일은 `ETC/` 또는 `misc/`로 모읍니다.
- 원본 프로젝트는 건드리지 않고, `refactored/projects/` 내부만 정리합니다.

## 프로젝트 목록
- `classification/` : 분류 실험과 데모 코드
- `detection_cv/` : 컴퓨터 비전 기반 탐지 실험
- `capstone/` : 캡스톤 관련 산출물
- `automl/` : 자동화 및 모델 시각화 자료
- `reinforcement_learning/` : 강화학습 관련 산출물
- `ETC/` : 포트폴리오용 요약 파일과 분류가 애매한 보조 자료

## 각 프로젝트 내부 예시
- `README.md` : 프로젝트 개요
- `docs/README.md` : 문서 인덱스
- `src/` 또는 `code/` : 실행 코드
- `docs/` : 설명 문서, 결과 요약, 참고자료

## 대표 요약 파일
포트폴리오에서 바로 확인하면 좋은 대표 요약 파일은 아래와 같습니다.

- `ETC/portfolio_click_detect.py`
- `ETC/portfolio_yolo_detection_summary.py`
- `ETC/portfolio_reinforcement_learning_summary.py`

## 안내
이 폴더는 GitHub 포트폴리오 공개용으로 정리한 구조입니다.
실행 코드와 설명 문서를 분리해 두어, 방문자가 프로젝트 흐름과 결과를 쉽게 확인할 수 있도록 구성했습니다.

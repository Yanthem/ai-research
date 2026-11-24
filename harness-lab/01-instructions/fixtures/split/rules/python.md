---
paths:
  - "**/*.py"
---
# Python 코드 규칙

## 버전과 도구
- Python 3.11 이상을 기준으로 쓴다.
- 포맷은 `ruff format`, 린트는 `ruff check`로 맞춘다. 커밋 전에 둘 다 통과해야 한다.
- 의존성은 `requirements.txt`(또는 `pyproject.toml`)에 버전과 함께 적는다. 예: `anthropic==0.80.0`.

## 이름
- 함수와 변수는 `snake_case`, 클래스는 `PascalCase`, 상수는 `UPPER_SNAKE_CASE`.
- 파일 이름은 하는 일을 동사로 시작한다. 예: `measure_tokens.py`, `run_relay.py`.

## 실험 스크립트의 모양
- 인자는 `argparse`로 받는다. 최소한 `--seed`와 `--model`을 노출한다.
- `if __name__ == "__main__":` 아래에서 `main()`만 부른다.
- 시드는 `random`, `numpy`(쓰는 경우)에 모두 넣는다.
- 출력 경로는 `outputs/<주제>/<날짜>-<짧은설명>/`으로 하고, 이 폴더는 커밋하지 않는다.
- 진행 상황은 `print` 대신 `logging`을 쓰고, 기본 레벨은 INFO.

## 예외와 재시도
- 네트워크 호출은 실패할 수 있다고 보고, 재시도 횟수와 대기 시간을 인자로 뺀다.
- 넓은 `except Exception:`으로 오류를 삼키지 않는다. 잡았다면 로그를 남기고 다시 던진다.

## 테스트
- 계산 로직은 함수로 분리해 `tests/` 아래 `pytest`로 확인할 수 있게 한다.
- 외부 API를 부르는 함수는 테스트에서 가짜 응답으로 바꿀 수 있게 클라이언트를 인자로 받는다.

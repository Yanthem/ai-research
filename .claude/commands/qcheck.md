---
description: 로컬 Qwen으로 빠른 중간 점검 (diff 리뷰 + 테스트/린트 요약)
argument-hint: [실행할 점검 명령, 예: pytest -q]
---

Claude 토큰을 아끼기 위한 빠른 점검이다. 직접 diff나 로그를 읽지 말고 Qwen 결과만 본다.

1. `mcp__crew__qwen_git`을 `action: "review"`로 부른다.
2. 점검 명령: `$ARGUMENTS`. 비어 있으면 프로젝트에 맞는 것을 하나 고른다 (Python이면 `ruff check .` 또는 `pytest -q`, 없으면 생략). 고른 명령을 `mcp__crew__qwen_run`으로 실행한다.
3. 결과를 5줄 이내로 보고한다. Qwen이 지적한 문제 중 진짜 문제로 보이는 것만 해당 파일을 열어 확인하고 고친다.
4. `.crew/CONTEXT.md`의 계획 상태를 갱신한다.

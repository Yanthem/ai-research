---
description: 옆 터미널의 Codex(GPT)에게 Reason Network로 교차 확인을 요청한다
argument-hint: [확인할 내용, 비우면 현재 diff와 계획]
---

확인 대상: $ARGUMENTS (비어 있으면 `git diff HEAD`와 .crew/CONTEXT.md의 계획)

1. `.crew/CONTEXT.md`의 "계획"과 "결정 사항"을 현재 상태로 갱신하고, 맨 아래 "## 검토 요청" 칸에 이번에 볼 대상(파일 경로, diff 범위)을 적는다.
2. `mcp__reason-network__list_team`으로 이 폴더의 Codex 세션 주소를 찾는다.
3. `mcp__reason-network__send_message`로 그 세션에 보낸다. 내 결론은 알려주지 않는다. 내용:
   "`.crew/CONTEXT.md`를 읽고 '검토 요청' 항목을 검토해 줘. 코드는 고치지 마. 가장 큰 위험 3개, 놓친 요구사항, 확실하지 않은 점을 짧게 답장해 줘."
4. Codex 세션이 없거나 도구가 없으면 Bash로 `codex exec -s read-only "<3번과 같은 요청>"`을 실행한다.
5. 답이 오면 내 계획과 비교해 `[합의] [GPT만 지적] [결정 필요]`로 정리하고, 고칠 것은 고친다. [결정 필요]는 나(사용자)에게 묻는다.

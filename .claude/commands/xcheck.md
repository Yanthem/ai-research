---
description: 지금까지의 변경이나 특정 결과물을 GPT에게 교차 확인받는다
argument-hint: [확인할 내용, 비우면 현재 diff]
---

확인 대상: $ARGUMENTS (비어 있으면 `git diff HEAD` 전체와 .crew/CONTEXT.md의 계획)

1. `.crew/CONTEXT.md`의 "계획"과 "결정 사항"을 현재 상태로 갱신한다.
2. gpt-crosscheck 서브에이전트에게 위 대상을 넘겨 검토를 맡긴다.
3. 돌아온 [합의] [GPT만 지적] [결정 필요]를 보고, 고칠 것은 바로 고치고 무엇을 고쳤는지 짧게 알려준다. [결정 필요]는 나에게 묻는다.

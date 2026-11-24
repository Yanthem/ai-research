---
description: 원격 변경을 받아오고(git pull) 무엇이 바뀌었는지 Qwen 요약으로 확인한다
---

1. `mcp__crew__qwen_git`을 `action: "status"`로 불러 로컬 변경이 있는지 본다. 커밋 안 된 변경이 있으면 pull하지 말고 나에게 알려준다.
2. 깨끗하면 `action: "pull"`로 부른다.
3. Qwen 요약을 3줄로 보여주고, 바뀐 내용이 .crew/CONTEXT.md의 계획에 영향을 주면 그 부분만 갱신한다.

# orchestra — Reason Network로 Claude·Codex(GPT)·Qwen 한 팀으로 쓰기

## 목적
wikidocs 「주말완성 Reason Network」(https://wikidocs.net/480853)의 방식을 따른다.
Claude Code와 Codex를 각자 터미널에서 따로 켜 두고, 두 에이전트가 **Reason Network로 서로의 대화에 직접 메시지를 넣는다.**
사람이 복사·붙여넣기로 중계하지 않는다. 로컬 Qwen은 Reason Network에 붙는 에이전트가 아니므로 Claude가 MCP 도구(`crew`)로 부린다.

```
   VS Code 터미널 1                          VS Code 터미널 2
   Claude Code (operator)  <== Reason Network ==>  Codex CLI (GPT, 검토 담당)
   계획 · 조율 · 핵심 코드     send_message / 자동 수신     독립 검토, 다른 시각
          |                                         |
          | crew MCP                                |
          v                                         |
   Qwen 3.5 9B (Ollama, 로컬)                       |
   요약 · 로그 · git · 1차 리뷰                      |
          \_____________ .crew/CONTEXT.md ___________/
                    (같은 폴더의 공용 메모)
```

## 용어 먼저
- **Reason Network**: 여러 코딩 에이전트(Claude Code, Codex, Grok 등)를 "팀"으로 묶어, 살아 있는 세션끼리 메시지를 주고받게 하는 오픈소스 도구. PC마다 백그라운드 프로그램(데몬)이 하나 돌고, 각 에이전트에는 MCP 서버와 훅으로 연결된다.
- **세션 주소**: 에이전트 대화 하나의 이름. 기본은 `<폴더>-<에이전트>`. 예: `contest-1125-claude`, `contest-1125-codex`.
- **push 전달**: Claude Code와 Codex는 메시지를 받으면 사람이 아무것도 치지 않아도 바로 읽고 답한다.
- **MCP 서버**: Claude Code에 새 도구를 붙여 주는 작은 프로그램. 여기서는 `reason-network`(팀 메시지)와 `crew`(Qwen)를 쓴다.
- **공유 컨텍스트**: `.crew/CONTEXT.md`. 과제, 계획, 결정을 적는 공용 메모. 두 에이전트가 같은 폴더에서 일하므로 둘 다 직접 읽는다. 처음 `/team-plan`을 실행하면 Claude가 만든다. `.gitignore`에 들어 있다.

## 파일 구성
| 파일 | 하는 일 |
|------|---------|
| `.mcp.json` | 이 저장소에서 `crew`(Qwen) MCP 서버 등록 |
| `.claude/settings.json` | Reason Network·Qwen 도구는 매번 묻지 않게 허용 |
| `.claude/commands/*.md` | `/team-plan`, `/xcheck`, `/qcheck`, `/sync` |
| `.claude/agents/qwen-worker.md` | 반복 작업을 Qwen에게 나눠 주는 서브에이전트 |
| `orchestra/crew_mcp.py` | Qwen MCP 서버 (표준 라이브러리만 사용) |
| `orchestra/CLAUDE.crew.md` | Claude가 지킬 역할 분담·Codex 대화 규칙 |
| `orchestra/install_user.ps1` | 위 구성을 다른 폴더(대회용)에서도 쓰게 PC 전체에 설치 |

---

## 설치

모든 명령은 VS Code 터미널(PowerShell)에서 한 줄씩 입력한다. `>>`가 보이면 앞 줄이 안 끝난 것이다.

### 1단계. 최신 설정 받기 (ai-research 폴더)
```powershell
git checkout main
git pull
```

### 2단계. Qwen 확인 (끝났으면 건너뛰기)
```powershell
python orchestra\crew_mcp.py --check
```
`[OK] Ollama 연결됨`과 `[OK] Codex CLI`가 보이면 된다.

### 3단계. Codex 최신으로
```powershell
npm install -g @openai/codex@latest
codex --version
codex login            # 로그인 안 했을 때만. ChatGPT 계정
```

### 4단계. Reason Network 설치
책 7장의 Windows 방법이다. 공식 설치 스크립트를 내려받아 바로 실행하는 방식이라, 걱정되면 주소를 브라우저로 먼저 열어 내용을 볼 수 있다.
```powershell
irm https://reasonmachines.com/network/install.ps1 | iex
```
이 스크립트는 두 가지를 한다.
1. `reason` 프로그램 설치 (Reason 전체 도구. `reason`만 치면 "Reason is ready"가 나온다)
2. 이어서 `reason network` 실행: 브라우저에서 Reason 계정(무료, Google·GitHub 등)으로 로그인하고 네트워크를 새로 만든 뒤, 네트워크 엔진 `reason-network`를 받아 Claude Code·Codex 설정에 MCP 서버와 훅을 넣는다.

2번이 실패했으면(예: EPERM 오류) **새 터미널**에서 아래를 한 줄씩 실행한다. 설치 직후의 터미널은 `reason` 명령을 모른다.
```powershell
Get-Process reason* -ErrorAction SilentlyContinue | Stop-Process
Remove-Item $HOME\.reason\network-sign-in.lock* -ErrorAction SilentlyContinue
reason network
```
끝나면 `Join the Reason Network: <링크>`가 나온다. 이 링크는 비밀번호처럼 남에게 보여 주지 않는다.

### 5단계. 점검
`reason-network` 명령은 4단계의 `reason network`가 **성공한 뒤에** 생긴다. VS Code를 완전히 껐다 켠 뒤 새 터미널에서:
```powershell
reason-network doctor
```
데몬, 팀 연결, Claude Code·Codex 배선이 OK인지 본다. 명령이 없다고 나오면 4단계가 아직 안 끝난 것이다. `reason help all` 화면을 보고 network 관련 명령을 확인한다.

### 6단계. PC 전체에 설치 (대회 폴더에서도 쓰기)
ai-research 폴더 터미널에서:
```powershell
powershell -ExecutionPolicy Bypass -File orchestra\install_user.ps1
mkdir $HOME\OneDrive\Desktop\Yant\contest-1125
```

### 7단계. 두 에이전트가 대화하는지 시험
1. VS Code에서 `contest-1125` 폴더를 연다.
2. 터미널 1: `codex` 실행. 처음에 훅 경고가 나오면 `/hooks`에서 **Trust all and continue**를 고른다. (Codex는 신뢰한 훅만 실행한다. 이걸 안 하면 메시지가 들어오지 않는다.)
3. 터미널 2 (패널 오른쪽 위 `+`): `claude` 실행. `/mcp`에서 `crew`와 `reason-network`가 connected인지 본다.
4. Claude에게 입력: `list_team으로 팀 세션 보여주고, codex 세션에 "안녕, 들리면 답장해줘"라고 보내줘`
5. 몇 초 뒤 Codex 창에 메시지가 들어가고, Codex의 답장이 Claude 창에 `<reason-message from=...>`로 들어오면 성공이다.

---

## 내일 하루 작업 흐름

| 시점 | 내가 하는 것 | 누가 일하나 |
|------|--------------|-------------|
| 시작 (5분) | Ollama 켜짐 확인 → VS Code로 contest 폴더 열기 → 터미널 1 `codex`, 터미널 2 `claude` → `/mcp` | - |
| 문제 받음 | Claude 창에 `/team-plan 문제 내용` | Qwen이 요구사항 추출 → Claude 계획 → Codex가 메시지로 검토 → Claude 확정 |
| 계획 확인 | 계획을 읽고 "좋아, 1단계부터" | 나 |
| 구현 | "1단계 진행해" | Claude |
| 기능 하나 끝날 때마다 | `/qcheck pytest -q` (테스트 없으면 `/qcheck`) | Qwen이 diff 리뷰·로그 요약 |
| 반복 작업 | "qwen-worker로 data 폴더 CSV 10개 컬럼 확인해" | Qwen |
| 계획·결정이 바뀔 때마다 | "CONTEXT.md 갱신해" | Claude. 이게 낡으면 Codex가 옛 계획을 검토한다 |
| 막혔을 때 (같은 버그 2번 실패) | `/xcheck 이 에러가 안 고쳐짐: ...` | Codex가 다른 시각으로 원인 제시 |
| 핵심 로직 완성 후, 제출 30분 전 | `/xcheck` | Codex가 놓친 요구사항·위험 점검 |
| `/compact` 직전 | "CONTEXT.md 최신으로 갱신해" → `/compact` | 계획은 파일에 남는다 |

- Codex 창은 켜 두기만 하면 된다. 내가 Codex 창에 직접 물어봐도 되고, Codex가 Claude에게 먼저 메시지를 보낼 수도 있다.
- 역할 기준: 생각이 필요하면 Claude, 두 번째 의견은 Codex, 읽고 세고 요약·실행만 하면 되면 Qwen.
- Codex 검토는 하루 3~5번이면 충분하다. Plus 한도는 Codex 창에서 `/status`로 확인.

---

## 문제 생겼을 때
| 증상 | 해결 |
|------|------|
| Claude가 Codex 세션을 못 찾음 | Codex 창이 켜져 있는지 확인. `reason-network who`로 세션 목록 확인 |
| Codex가 메시지를 안 받음 | Codex에서 `/hooks` → Trust all. 그래도 안 되면 `reason-network doctor` |
| Reason Network 자체가 안 됨 | 대체 경로: Claude가 `codex exec -s read-only "요청"`으로 한 번씩 묻는다 (`/xcheck`에 들어 있음) |
| `/mcp`에서 crew가 failed | `python orchestra\crew_mcp.py --check`. `python`이 안 되면 `.mcp.json`의 `"python"`을 `"py"`로 |
| `[Qwen 연결 실패]` | Ollama 앱(트레이 아이콘) 켜기 |
| Qwen이 너무 느림 | `.mcp.json`의 `QWEN_CTX`를 `8192`로 |
| GPT "usage limit" | Codex에서 `/status`로 다시 차는 시각 확인. 그동안 Claude 혼자 진행, 제출 전 검토만 Codex에게 |
| 작업 중 MCP가 끊김 | Claude에게 "MCP 없이 계속해". `/mcp`에서 Reconnect |
| `ollama` 명령을 못 찾음 | VS Code를 껐다 켜기. 우리 구성은 Ollama 앱에 직접 연결하므로 작업에는 지장 없음 |

## 이전 버전과 달라진 점 (2026-11-25)
- 처음 버전은 `codex mcp-server`로 Codex를 MCP 도구처럼 불렀다. 이 명령은 Codex 0.154.0(2026-09-05)에서 없어졌다(책 4장). 최신 Codex에서 연결이 끊긴 원인이다.
- 그래서 책의 방식대로 Reason Network로 바꿨다. `gpt-crosscheck` 서브에이전트와 `.mcp.json`의 `codex` 항목은 지웠다.

## 결과 요약
- 2026-11-24: `crew_mcp.py`를 클라우드에서 가짜 Ollama 서버로 시험. 사용자 PC(Windows)에서 `--check` 통과(qwen3.5:9b 응답 확인), Claude Code `/mcp`에서 crew 연결 확인.
- 2026-11-25: Reason Network 구성은 책(기준 Reason Network 0.12.17, Codex 0.167.0, Claude Code 2.1.319) 내용을 따랐고, 사용자 PC에서는 아직 시험 전이다.
- 기본값: `QWEN_MODEL=qwen3.5:9b`, `QWEN_CTX=16384`, `temperature=0.2`, `seed=42`.

# orchestra — Claude·GPT·Qwen 한 팀으로 쓰기

## 목적
Claude Code 하나를 "운영자(operator)"로 두고, 그 안에서 GPT와 로컬 Qwen을 도구처럼 불러 쓴다.
창 세 개를 오가며 복사·붙여넣기 하지 않아도 되고, 비싼 Claude 토큰은 판단이 필요한 일에만 쓴다.

```
                 나 (VS Code 터미널)
                        |
               Claude Code (operator)
        계획 · 조율 · 핵심 코드 · 최종 결정
          /                          \
   codex MCP / crew.gpt          crew MCP (로컬)
   GPT: 교차 확인                Qwen 3.5 9B: 요약, 로그, git, 1차 리뷰
          \                          /
            .crew/CONTEXT.md  (세 AI 공용 메모 = Reason network의 공유 컨텍스트)
```

## 용어 먼저
- **MCP 서버**: Claude Code에 "새 도구"를 붙여 주는 작은 프로그램. 여기서는 두 개를 붙인다.
  - `crew` (이 폴더의 `crew_mcp.py`): Qwen 부르기, git, 명령 실행 후 요약, GPT API 호출
  - `codex`: OpenAI Codex CLI가 기본으로 제공하는 MCP 서버. ChatGPT 구독으로 GPT를 부른다.
- **서브에이전트**: Claude가 일을 맡기는 "부하 Claude". 자기 대화창이 따로 있어서 메인 대화가 길어지지 않는다.
  - `qwen-worker`: 반복 작업을 Qwen에게 나눠 주고 결과만 짧게 보고
  - `gpt-crosscheck`: GPT에게 독립 검토를 받아 Claude 의견과 비교
- **커맨드**: `/이름`으로 부르는 미리 써 둔 지시문. `/team-plan`, `/xcheck`, `/qcheck`, `/sync`
- **공유 컨텍스트**: `.crew/CONTEXT.md`. 과제, 계획, 결정을 적어 두는 공용 메모. GPT에게 보낼 때 자동으로 같이 간다.

## 파일 구성
| 파일 | 하는 일 |
|------|---------|
| `.mcp.json` | 이 저장소에서 `crew`, `codex` MCP 서버를 자동 등록 |
| `.claude/settings.json` | 위 서버 허용, 자주 쓰는 도구는 매번 묻지 않게 |
| `.claude/agents/*.md` | 서브에이전트 2개 |
| `.claude/commands/*.md` | 커맨드 4개 |
| `orchestra/crew_mcp.py` | Qwen/GPT MCP 서버 (표준 라이브러리만 사용, pip 설치 불필요) |
| `orchestra/CLAUDE.crew.md` | Claude가 지킬 역할 분담 규칙 (CLAUDE.md에서 불러옴) |
| `orchestra/install_user.ps1` | 위 구성을 다른 폴더(대회용)에서도 쓰도록 PC 전체에 설치 |

---

## 설치 (오늘 밤, 약 15분)

모든 명령은 VS Code에서 `` Ctrl+` `` 로 연 터미널(PowerShell)에 입력한다.

### 1단계. 브랜치 받기
```powershell
cd $HOME\OneDrive\Desktop\Yant\ai-research\ai-research
git fetch origin
git checkout claude/project-thread-22m7jp     # PR을 merge했다면: git checkout main; git pull
```

### 2단계. Qwen 준비 확인
```powershell
ollama list                      # qwen3.5:9b 가 보여야 한다
ollama pull qwen3.5:9b           # 없을 때만
```
`ollama list`에 다른 이름(예: `qwen3.5:9b-q4_K_M`)으로 있으면 `.mcp.json`의 `QWEN_MODEL` 값을 그 이름으로 바꾼다.

### 3단계. GPT 연결 방식 고르기 (둘 중 하나)
- **A. Codex CLI (권장, ChatGPT 구독 사용)**
  ```powershell
  codex --version       # 없으면: npm install -g @openai/codex
  codex login           # 처음 한 번, 브라우저에서 ChatGPT 계정으로 로그인
  ```
- **B. OpenAI API 키** (지난번 `measure_tokens.py`에서 쓴 방식, 토큰당 과금)
  ```powershell
  setx OPENAI_API_KEY "sk-..."     # 실행 후 VS Code를 완전히 껐다 켠다
  ```
  키는 절대 파일에 적어 커밋하지 않는다.

### 4단계. 연결 점검
```powershell
python orchestra\crew_mcp.py --check
```
`[OK] Ollama 연결됨`, Qwen 응답 시험 줄, Codex 또는 API 키 중 하나가 `[OK]`면 된다.

### 5단계. Claude Code에서 확인
```powershell
claude
```
- 처음 실행하면 "이 프로젝트의 MCP 서버를 허용할까?"라고 묻는다. 허용한다.
- `/mcp` 입력 → `crew`, `codex`가 `connected`인지 본다. (B 방식이면 `codex`는 failed여도 괜찮다)
- `/agents` 입력 → `qwen-worker`, `gpt-crosscheck`가 보이는지 본다.
- 시험: `crew의 qwen 도구로 CLAUDE.md를 3줄 요약해줘`

### 6단계. 대회용 폴더에서도 쓰기
대회 코드가 이 저장소가 아닌 다른 폴더라면 한 번만 실행한다.
```powershell
powershell -ExecutionPolicy Bypass -File orchestra\install_user.ps1
```
커맨드·서브에이전트·MCP 서버·역할 규칙이 PC 전체(`~\.claude`)에 설치되어, 어느 폴더에서 `claude`를 켜도 똑같이 쓸 수 있다.

---

## 내일 하루 작업 흐름

| 시점 | 내가 입력하는 것 | 누가 일하나 |
|------|------------------|-------------|
| 시작 (5분) | Ollama 앱 켜기 → VS Code에서 대회 폴더 열기 → `claude` → `/mcp` → `/sync` (git 폴더일 때) | Qwen이 최신 상태 확인 |
| 문제 받음 | `/team-plan 문제.md` (또는 문제 내용 붙여넣기) | Qwen이 요구사항 추출 → Claude 계획 → GPT 검토 → Claude 확정 |
| 계획 확인 | 계획을 읽고 "좋아, 1단계부터" | 나 |
| 구현 | 단계별로 "1단계 진행해" | Claude가 코드 작성 |
| 기능 하나 끝날 때마다 | `/qcheck pytest -q` (테스트 없으면 `/qcheck`) | Qwen이 diff 리뷰·테스트 로그 요약, Claude는 지적된 곳만 확인 |
| 반복 작업 | "qwen-worker로 data 폴더 CSV 10개 컬럼 형식 확인해" | Qwen |
| 팀원이 push했을 때, 1~2시간마다 | `/sync` | Qwen이 pull 후 변경 요약 |
| 막혔을 때 (같은 버그 2번 실패) | `/xcheck 이 에러가 안 고쳐짐: ...` | GPT가 다른 시각으로 원인 제시 |
| 핵심 로직 완성 후, 제출 30분 전 | `/xcheck` | GPT가 놓친 요구사항·위험 점검 |
| 계획·결정이 바뀔 때마다 | "CONTEXT.md 갱신해" | Claude가 공유 메모를 고친다. 이게 낡으면 GPT가 옛 계획을 검토한다 |
| `/compact` 직전 | "CONTEXT.md 최신인지 확인하고 갱신해" → `/compact` | 대화를 압축해도 계획은 CONTEXT.md에 남는다 |

### 역할을 고르는 기준 한 줄
- 생각이 필요하면 Claude, 두 번째 의견이 필요하면 GPT, 읽고 세고 요약하고 실행만 하면 되면 Qwen.

### 토큰과 시간 아끼는 요령
- 긴 문서·로그를 Claude 창에 붙여넣지 말고 "qwen으로 이 파일 요약해" 라고 경로만 준다. 파일 내용은 Qwen 서버가 직접 읽는다.
- GPT 교차 확인은 하루 3~5번이면 충분하다 (계획, 핵심 로직, 막힐 때, 제출 전).
- Qwen 답은 1차 필터다. Claude가 문제라고 표시된 곳만 다시 확인하도록 규칙에 적어 두었다.

---

## 문제 생겼을 때
| 증상 | 해결 |
|------|------|
| `/mcp`에서 crew가 failed | 터미널에서 `python orchestra\crew_mcp.py --check` 로 오류 확인. `python`이 안 되면 `.mcp.json`의 `"python"`을 `"py"`로 |
| `[Qwen 연결 실패]` | Ollama 앱(트레이 아이콘)을 켜거나 `ollama serve` |
| Qwen이 너무 느림 | `.mcp.json`의 `QWEN_CTX`를 `8192`로 줄인다 (8GB VRAM 기준) |
| codex가 failed | `codex --version`, `codex login` 확인. 안 되면 B 방식(API 키)으로 `crew`의 `gpt` 도구 사용 |
| GPT 오류 "model requires a newer version of Codex" | Claude Code를 `/exit` → `npm install -g @openai/codex@latest` → `claude` 다시 실행 |
| GPT 오류 "usage limit" (한도 초과) | Codex에서 `/status`로 다시 차는 시각 확인. 그동안은 Claude 혼자 진행하고, 제출 전 검토만 GPT에게 |
| 작업 중 crew나 codex가 끊김 | Claude에게 "MCP 없이 계속해"라고 하면 Claude가 직접 처리한다. `/mcp`에서 해당 서버를 골라 Reconnect |
| 매번 허용 여부를 물음 | 물을 때 "Yes, don't ask again" 선택. `qwen_run`은 명령을 실행하므로 일부러 묻게 두었다 |
| 다른 폴더에서 git 작업이 엉뚱한 곳에서 됨 | 그 폴더에서 `claude`를 켰는지 확인. 필요하면 MCP 등록 시 `-e CREW_ROOT=폴더경로` 추가 |

## 결과 요약
- 2026-11-24 작성. `crew_mcp.py`는 클라우드에서 가짜 Ollama 서버로 MCP 연결, 도구 목록, 4개 도구 호출을 시험했다. 실제 Windows·Ollama·Codex 환경 시험은 아직이다.
- 기본값: `QWEN_MODEL=qwen3.5:9b`, `QWEN_CTX=16384`, `temperature=0.2`, `seed=42`, `GPT_MODEL=gpt-5`(API 방식일 때).

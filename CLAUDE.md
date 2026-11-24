# 프로젝트 설정 (ai 연구회)

## 프로젝트 개요
- **이름**: ai-research — AI 연구회 공용 저장소
- **목적**: 멀티 에이전트 / 모델 오케스트레이션, 에이전트 검색(RAG, DCI 등), 코딩 에이전트 도구에 대한 실험 코드와 연구 노트 보관
- **주 언어**: Python (실험·측정 스크립트), Markdown (노트·정리)
- **응답 언어**: 한국어로 답한다. 코드, 명령어, 식별자는 영어 그대로 둔다.

## 디렉터리 규칙
- 주제별로 최상위 폴더를 하나씩 만든다 (예: `reason-network/`).
- 각 주제 폴더에는 `README.md`를 두고 목적, 실행 방법, 결과 요약을 적는다.
- 논문 정리는 `papers/<arXiv-ID 또는 짧은-이름>.md` 형식으로 둔다.
- 대용량 데이터, 모델 가중치, 결과 산출물은 커밋하지 않는다 (`data/`, `outputs/`는 `.gitignore`).

## 코드 스타일 (Python)
- Python 3.11+, 포맷은 `ruff format`, 린트는 `ruff check`
- 함수/변수는 `snake_case`, 클래스는 `PascalCase`, 상수는 `UPPER_SNAKE_CASE`
- 실험 스크립트는 `argparse`로 인자를 받고, 시드와 모델 이름을 인자로 노출한다.
- 의존성은 `requirements.txt`(또는 `pyproject.toml`)에 버전과 함께 적는다.

## 실험 재현성
- 실험 결과를 적을 때는 모델 ID, 날짜, 주요 하이퍼파라미터, 시드를 함께 남긴다.
- 숫자를 인용할 때는 출처(논문, 링크, 스크립트 경로)를 붙인다.
- 비용이 드는 API 호출은 실행 전에 예상 토큰 수/비용을 먼저 계산한다.

## 보안
- API 키는 절대 하드코딩하거나 커밋하지 않는다. 환경 변수(`ANTHROPIC_API_KEY` 등)나 `.env`(커밋 금지)를 쓴다.

## Git 작업 방식
- 브랜치 이름: `exp/설명`, `notes/설명`, `fix/설명`
- 커밋 메시지는 Conventional Commits 형식 (`feat:`, `fix:`, `docs:`, `exp:` 등)
- `main`에 직접 푸시하지 않고 PR로 합친다.

## Claude Code 설정
- `/optimize` — 코드 성능 문제 분석 (`.claude/commands/optimize.md`)
- `code-review-specialist` 스킬 — 코드 리뷰 요청 시 자동 사용 (`.claude/skills/code-review-specialist/`)
- 둘 다 프로젝트 수준이라 클라우드 세션에서도 그대로 동작한다.

## 자주 쓰는 명령

| 명령 | 용도 |
|------|------|
| `pip install -r requirements.txt` | 의존성 설치 |
| `ruff check . && ruff format --check .` | 린트/포맷 확인 |
| `python <주제>/<스크립트>.py --help` | 실험 스크립트 사용법 확인 |

## 멀티 AI 팀 구성 (orchestra/)
- 역할 분담과 운영 규칙: @orchestra/CLAUDE.crew.md
- 커맨드: `/team-plan`, `/xcheck`, `/qcheck`, `/sync` / 서브에이전트: `qwen-worker`, `gpt-crosscheck`
- 설치와 하루 작업 흐름: `orchestra/README.md`

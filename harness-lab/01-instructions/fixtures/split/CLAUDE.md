# ai-research (AI 연구회 공용 저장소)

## 개요
멀티 에이전트 오케스트레이션, 에이전트 검색(RAG, DCI), 코딩 에이전트 도구에 대한 실험 코드와 연구 노트를 둔다.
답은 한국어로 쓰고, 코드·명령·식별자는 영어 그대로 둔다.

## 빠른 시작
- 설치: `pip install -r requirements.txt`
- 린트: `ruff check . && ruff format --check .`
- 스크립트 사용법: `python <주제>/<스크립트>.py --help`

## 강제 규칙 (예외 없음)
1. API 키를 코드나 커밋에 넣지 않는다. 환경 변수나 `.env`(커밋 금지)만 쓴다.
2. `main`에 직접 푸시하지 않는다. `exp/`, `notes/`, `fix/` 브랜치에서 PR로 합친다.
3. 커밋 메시지는 Conventional Commits(`feat:`, `fix:`, `docs:`, `exp:`)를 따른다.
4. `data/`, `outputs/`, 모델 가중치는 커밋하지 않는다.
5. 비용이 드는 API 호출 전에는 예상 토큰과 비용을 먼저 계산해 보여 준다.

## 주제 문서 (필요할 때만 읽기)
- `rules/python.md` — Python 파일을 만들거나 고칠 때
- `rules/experiments.md` — 실험 결과나 README를 쓸 때
- `rules/papers.md` — `papers/` 아래 논문 노트를 쓸 때
- `rules/api-cost.md` — 유료 API를 호출하는 코드를 쓸 때

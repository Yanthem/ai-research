# 01. 지시 설계: 입구 파일과 규칙 분리

## 목적
CLAUDE.md 한 파일에 규칙을 다 넣는 방식(A)과, 짧은 입구 파일에 주제 문서를 나누는 방식(B, C)이
작업마다 컨텍스트에 실제로 얼마나 다른 양의 지시를 넣는지 잰다.

| 방식 | 구성 | 언제 읽히나 |
|---|---|---|
| A monolith | CLAUDE.md 하나에 모든 규칙 | 항상 전부 |
| B entry+links | 입구 CLAUDE.md + `rules/*.md` 링크 | 입구는 항상, 주제 문서는 에이전트가 골라 읽을 때 |
| C entry+rules | 입구 CLAUDE.md + `.claude/rules/*.md` (`paths:` 프런트매터) | 입구는 항상, 규칙은 건드린 파일 경로가 맞을 때 자동 |

## 실행 방법
```
python harness-lab/01-instructions/measure_instructions.py            # 근사치, API 호출 없음
python harness-lab/01-instructions/measure_instructions.py --check    # 입구 파일 줄 수, 강제 규칙 수, 링크, 중복 점검
python harness-lab/01-instructions/measure_instructions.py --counter claude --model claude-opus-5-5   # 정확한 토큰 (count_tokens, 생성 비용 없음)
python harness-lab/01-instructions/measure_instructions.py --json     # 표 대신 JSON
```
입력: `fixtures/split/` (입구 파일 + 규칙 4개), `fixtures/tasks.json` (작업 5개와 각 작업에 필요한 규칙).

## 결과 요약
2026-11-24, `--counter approx`(한글 1자=1토큰, ASCII 4자=1토큰 근사), 시드 0, 단가 입력 $4/MTok, 캐시 읽기 $0.20/MTok, 월 100세션 x 20턴.

| 방식 | 평균 지시 토큰 | A 대비 | 신호 대 잡음(SNR) | 빠진 규칙 | 월 지시 비용 |
|---|---|---|---|---|---|
| A monolith | 1,703 | 100% | 44% | 0 | $1.50 |
| B entry+links | 755 | 44% | 100% | 0 | $0.66 |
| C entry+rules | 893 | 52% | 85% | 0 | $0.79 |

- 분리하면 작업당 지시 토큰이 절반 아래로 준다. 차이는 규칙이 늘수록 커진다(A만 규칙 수에 비례해 커짐).
- 돈 차이는 작다(프롬프트 캐싱 때문). 진짜 이득은 컨텍스트 여유와 "지금 필요 없는 규칙"이 주의를 뺏지 않는 것.
- C의 오탐 2건: 루트 `README.md` 수정(T4)에 `experiments.md`가, 리팩터(T5)에 `api-cost.md`가 함께 읽혔다. 글롭을 좁히면 줄어든다.

## 한계
- B의 100%는 "에이전트가 필요한 문서를 정확히 골라 읽는다"는 가정이다. 실제로는 안 읽거나 더 읽을 수 있다. 그래서 강제 규칙 5개는 입구 파일에 직접 둔다.
- 작업 5개, 규칙 4개짜리 작은 예제다. 토큰 수는 근사치이며 `--counter claude`로 다시 재야 정확하다.
- 지시 토큰만 쟀다. 지시가 짧아져서 출력 품질이 실제로 좋아지는지는 2단계 이후 평가 실험으로 확인한다.

## 출처
- 하네스 엔지니어링 책(wikidocs 21997) 4장: 입구 파일 50~200줄, 강제 규칙 15개 이하, 점진적 공개.
- Claude Code Howto(wikidocs 21956) 메모리 장: `.claude/rules/*.md`의 `paths:` 프런트매터, 로딩 순서.

# agentic-search: DCI와 DR-DCI를 우리 공부 자료에 적용하기

## 목적
두 논문의 주장을 우리 환경에서 확인한다.
- DCI(arXiv 2605.05242): 검색기 없이 에이전트가 grep/rg와 read로 원문 폴더를 직접 탐색하면 RAG보다 낫다.
- DR-DCI(arXiv 2606.14885): 코퍼스가 커지면 grep만으로는 느리고 출력이 넘치므로, 검색기로 문서를 작업 폴더에 끌어온 뒤(pull) 그 안에서 grep 한다.

논문 정리: `papers/2605.05242.md`, `papers/2606.14885.md`. 실제 사용은 `.claude/skills/dci-search/` 스킬.

## 코퍼스
공부 중인 두 책의 한국어판 원본 저장소(둘 다 MIT).
- Claude Code Howto: github.com/luongnv89/claude-howto 의 `ko/` (98개 문서)
- 하네스 엔지니어링: github.com/walkinglabs/learn-harness-engineering 의 `docs/ko/` (105개 문서)
합계 203개 문서, 약 120만 자. `data/`는 커밋하지 않는다.

## 실행
```
git clone --depth 1 https://github.com/luongnv89/claude-howto ../_src/claude-howto
git clone --depth 1 https://github.com/walkinglabs/learn-harness-engineering ../_src/harness
python agentic-search/build_corpus.py --src howto=../_src/claude-howto/ko --src harness=../_src/harness/docs/ko
python agentic-search/eval_retrieval.py --k 5      # RAG(청크) vs pull(문서) 검색 단계 비교
python agentic-search/grep_probe.py                # grep 첫 수 흉내
python agentic-search/pull.py "훅 종료 코드 2" --k 8   # DR-DCI pull 도구
```
규모 실험은 전 언어판(2,410개 문서)을 `data/corpus_all/`에 모은 뒤 `python agentic-search/scale_bench.py --factors 1 5 20`.
외부 패키지는 없다(표준 라이브러리 + ripgrep). Claude Code에는 ripgrep이 들어 있고, 터미널에서 쓰려면 `winget install BurntSushi.ripgrep.MSVC`.

## 결과 요약 (2026-11-24, 클라우드 Linux 4코어, 시드 없음·결정적)
질문 12개는 코퍼스를 보기 전에 학습자 관점에서 썼고, 정답 문서는 그 뒤 rg로 확인했다(`questions.json`). 표본이 작아 경향만 본다.

검색 단계 (`eval_retrieval.py`, 청크 1000자):

| 방식 | 토크나이저 | 정답 문서 포함 | 정답 문장 포함 | LLM에 넘기는 양 |
|---|---|---|---|---|
| RAG 청크 top-5 | 공백 | 9/12 | 8/12 | 평균 4,872자 |
| RAG 청크 top-5 | 2글자 | 9/12 | 7/12 | 평균 4,939자 |
| RAG 청크 top-10 | 2글자 | 11/12 | 9/12 | 평균 9,939자 |
| pull 문서 top-8 (DR-DCI 첫 단계) | 2글자 | 12/12 | (이후 grep) | 미리보기만 |

grep 첫 수 (`grep_probe.py`, 미리 적은 키워드 그대로): 정답 문서 1위 9/12, 5위 안 11/12, 첫 출력 평균 2,895자(20줄, `rg --sort path`로 순서 고정).
놓친 1개(q10)는 영어 키워드 `maker/checker`로 한국어 본문 `메이커/체커`를 못 찾은 경우다.

규모 (`scale_bench.py`, 질의 3개 평균):

| 배수 | 문서 수 | 크기 | 전체 rg 시간 | 전체 rg 출력 | pull top-20 시간 | workspace rg 출력 | BM25 인덱스 구축 |
|---|---|---|---|---|---|---|---|
| 1 | 2,410 | 17MB | 0.016초 | 171줄 / 38KB | 0.01초 | 15줄 / 2.4KB | 1.6초 |
| 5 | 12,050 | 86MB | 0.057초 | 857줄 / 188KB | 0.04초 | 53줄 / 8.5KB | 7.0초 |
| 20 | 48,200 | 345MB | 0.197초 | 3,427줄 / 753KB | 0.19초 | 140줄 / 27KB | 26.6초 |

읽는 법
- 우리 코퍼스(1.2MB)에서는 문서를 찾는 것 자체는 어렵지 않다. pull 문서 top-8이 12/12. RAG가 지는 지점은 청크로 자르면서 정답 문장이 빠지는 단계다(문서 9~11/12 → 문장 7~9/12). DCI 논문의 "초기 필터링이 근거를 버린다"는 주장과 같은 방향이다.
- grep 속도는 345MB에서도 0.2초다. 큰 코퍼스에서 문제는 속도보다 **출력 양**이다. 한 번에 753KB가 나오면 에이전트 컨텍스트를 채운다. DR-DCI의 pull은 이를 27KB로 줄였다. 복제본으로 키운 코퍼스라 중복 문서가 섞여 있다는 한계가 있다.
- 결론: 지금 규모에서는 DR-DCI 없이 DCI(Claude Code + dci-search 스킬)로 충분하다. 수만 문서 이상이거나 grep 출력이 수천 줄이면 pull을 붙인다.
- 정확도(최종 답) 비교는 LLM을 돌려야 하므로 아직 하지 않았다. 다음 단계에 적는다.

## 다음 단계
1. Claude Code에서 dci-search 스킬로 12문제를 풀고, 답·인용·도구 호출 수를 기록한다(정답 판정은 사람).
2. 같은 12문제를 로컬 Ollama 모델(qwen3.5:9b)에 grep/read 도구만 주고 풀게 해 본다. 작은 모델이 도구 루프를 버티는지가 관건이다. 논문은 소형·로컬 모델을 시험하지 않았다.
3. 질문을 30개 이상으로 늘리고, 질문 작성자와 채점자를 분리한다.

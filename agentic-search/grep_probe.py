"""DCI의 첫 수를 흉내 낸 스크립트 탐색(LLM 없음).

에이전트가 가장 많이 쓰는 첫 명령은 `rg 키워드 | head` 다(DCI 논문 부록 B.1: rg|head 56%).
여기서는 질문을 보기만 하고 코퍼스를 보기 전에 적어 둔 keywords(questions.json)로 rg -c 를 돌려
파일을 일치 수로 줄 세우고, 정답 문서가 몇 위에 오는지와 에이전트가 읽게 될 출력 크기를 잰다.
진짜 에이전트는 결과를 보고 키워드를 바꾸므로 이 수치는 "첫 시도"의 하한선이다.

예: python agentic-search/grep_probe.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path


def rg(args: list[str], cwd: Path) -> str:
    return subprocess.run(
        ["rg", "--sort", "path", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    ).stdout


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--questions", default="agentic-search/questions.json")
    ap.add_argument(
        "--head", type=int, default=20, help="rg -n 출력에서 에이전트가 보는 줄 수"
    )
    args = ap.parse_args()

    corpus = Path(args.corpus)
    qs = json.loads(Path(args.questions).read_text(encoding="utf-8"))["questions"]
    top1 = top5 = 0
    total_obs = 0
    print("id   정답순위  후보파일수  첫관찰(자)  키워드")
    for q in qs:
        counts: Counter = Counter()
        for kw in q["keywords"]:
            for line in rg(["-c", "-i", "-F", "--", kw, "."], corpus).splitlines():
                path, _, n = line.rpartition(":")
                counts[path.replace("\\", "/").removeprefix("./")] += int(n)
        ranked = [p for p, _ in counts.most_common()]
        rank = next((i + 1 for i, p in enumerate(ranked) if p in q["gold_files"]), None)
        first = "\n".join(
            rg(["-n", "-i", "-F", "--", q["keywords"][0], "."], corpus).splitlines()[
                : args.head
            ]
        )
        total_obs += len(first)
        top1 += rank == 1
        top5 += rank is not None and rank <= 5
        print(
            f"{q['id']}  {rank!s:>6}  {len(ranked):>9}  {len(first):>9,}  {q['keywords']}"
        )
    n = len(qs)
    print(
        f"\n정답 문서 1위 {top1}/{n}, 5위 안 {top5}/{n}, 첫 관찰 평균 {total_obs // n:,}자 (head {args.head}줄)"
    )


if __name__ == "__main__":
    main()

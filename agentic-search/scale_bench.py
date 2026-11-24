"""코퍼스가 커질 때 DCI(전체 grep)와 DR-DCI(pull 뒤 workspace grep)의 비용이 어떻게 변하는지 잰다. LLM 없음.

기준 코퍼스(공부 자료 전 언어판)를 N배로 복제해 키운다. 복제본은 파일 앞에 다른 머리말을 붙여
완전히 같은 파일이 되지 않게 한다. 재는 것:
- DCI: 전체 코퍼스에 `rg -n 키워드` 한 번의 시간과 출력 크기(에이전트가 받게 되는 양)
- DR-DCI: BM25 pull(top-k) 시간 + workspace 안 `rg -n` 시간과 출력 크기

예: python agentic-search/scale_bench.py --base data/corpus_all --factors 1 5 20
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from pathlib import Path

from corpus_tools import BM25, load_corpus

QUERIES = [
    ("종료 코드 2", "훅에서 종료 코드 2를 반환하면 어떻게 되나"),
    (".mcp.json", "MCP 서버를 프로젝트 범위로 추가하면 설정 파일"),
    ("PROGRESS.md", "여러 세션에 걸쳐 작업을 이어가는 진행 기록"),
]


def grow(base: Path, out: Path, factor: int) -> None:
    if out.exists():
        shutil.rmtree(out)
    for i in range(factor):
        for p in base.rglob("*.md"):
            dest = out / f"copy{i:03d}" / p.relative_to(base)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(
                f"<!-- copy {i} -->\n"
                + p.read_text(encoding="utf-8", errors="replace"),
                encoding="utf-8",
            )


def timed_rg(pattern: str, where: Path) -> tuple[float, int, int]:
    t = time.perf_counter()
    r = subprocess.run(
        ["rg", "-n", "-F", "--", pattern, "."],
        cwd=where,
        capture_output=True,
        check=False,
    )
    lines = r.stdout.count(b"\n")
    return time.perf_counter() - t, lines, len(r.stdout)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--base", default="data/corpus_all")
    ap.add_argument("--factors", type=int, nargs="+", default=[1, 5, 20])
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--work", default="data/scale")
    args = ap.parse_args()

    print(
        "배수  문서수  크기MB | DCI rg초  출력줄  출력KB | pull초  ws-rg초  출력줄  출력KB | 인덱스구축초"
    )
    for f in args.factors:
        corpus = Path(args.work) / f"x{f}"
        grow(Path(args.base), corpus, f)
        files = list(corpus.rglob("*.md"))
        mb = sum(p.stat().st_size for p in files) / 1e6
        t = time.perf_counter()
        index = BM25(load_corpus(corpus))
        build = time.perf_counter() - t
        agg = [0.0] * 7
        for kw, q in QUERIES:
            dci_t, dci_lines, dci_bytes = timed_rg(kw, corpus)
            t = time.perf_counter()
            hits = index.search(q, args.k)
            ws = Path(args.work) / "ws"
            shutil.rmtree(ws, ignore_errors=True)
            ws.mkdir(parents=True)
            for n, (_, d) in enumerate(hits):
                shutil.copyfile(corpus / d.doc_id, ws / f"{n:02d}.md")
            pull_t = time.perf_counter() - t
            ws_t, ws_lines, ws_bytes = timed_rg(kw, ws)
            for i, v in enumerate(
                [
                    dci_t,
                    dci_lines,
                    dci_bytes / 1e3,
                    pull_t,
                    ws_t,
                    ws_lines,
                    ws_bytes / 1e3,
                ]
            ):
                agg[i] += v / len(QUERIES)
        print(
            f"{f:>3}  {len(files):>6}  {mb:6.1f} | {agg[0]:7.3f}  {agg[1]:6.0f}  {agg[2]:6.0f} | "
            f"{agg[3]:6.2f}  {agg[4]:7.3f}  {agg[5]:6.0f}  {agg[6]:6.1f} | {build:8.1f}"
        )
        shutil.rmtree(corpus)


if __name__ == "__main__":
    main()

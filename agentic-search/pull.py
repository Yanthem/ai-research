"""DR-DCI의 pull(query, topK)를 흉내 낸 작은 CLI.

전체 코퍼스(에이전트에게 숨김)에서 BM25로 문서 topK개를 골라 작업 폴더(workspace)로 복사하고,
순위 미리보기를 출력한다. 에이전트는 그다음 workspace 안에서만 rg/Grep, Read로 탐색한다.
같은 문서를 다시 끌어오면 중복으로 세지 않는다. 다시 부르면 workspace가 점점 넓어진다.

예:
  python agentic-search/pull.py "훅 종료 코드 2 차단" --k 8
  python agentic-search/pull.py --reset            # workspace 비우기
"""

from __future__ import annotations

import argparse
import pickle
import re
import shutil
from pathlib import Path

from corpus_tools import BM25, load_corpus, tokenize

PREVIEW_CHARS = 160
NOISE = re.compile(r"<!--.*?-->|<[^>]+>", re.DOTALL)


def preview(text: str, query: str) -> str:
    """제목 한 줄 + 질의 토큰이 가장 많이 겹치는 줄 하나."""
    clean = NOISE.sub("", text)
    lines = [ln.strip() for ln in clean.splitlines() if ln.strip()]
    title = next((ln.lstrip("# ") for ln in lines if ln.startswith("#")), "")
    q = set(tokenize(query))
    best = max(lines, key=lambda ln: len(q & set(tokenize(ln))), default="")
    return f"{title} | {best}"[:PREVIEW_CHARS]


def load_index(corpus: Path, mode: str) -> BM25:
    cache = corpus.parent / f".bm25-{corpus.name}-{mode}.pkl"
    newest = max((p.stat().st_mtime for p in corpus.rglob("*.md")), default=0)
    if cache.exists() and cache.stat().st_mtime > newest:
        with cache.open("rb") as f:
            return pickle.load(f)
    index = BM25(load_corpus(corpus), mode=mode)
    with cache.open("wb") as f:
        pickle.dump(index, f)
    return index


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("query", nargs="?")
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--workspace", default="data/workspace")
    ap.add_argument("--tokenizer", choices=["bigram", "space"], default="bigram")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    ws = Path(args.workspace)
    if args.reset:
        shutil.rmtree(ws, ignore_errors=True)
        print(f"{ws} 비움")
        return
    if not args.query:
        ap.error("query가 필요합니다")

    index = load_index(Path(args.corpus), args.tokenizer)
    ws.mkdir(parents=True, exist_ok=True)
    new = 0
    for rank, (score, doc) in enumerate(index.search(args.query, args.k), 1):
        # 파일 이름을 평평하게 만들어 workspace 한 폴더에 모은다(DR-DCI의 root-flat 폴더).
        flat = doc.doc_id.replace("/", "__").replace("\\", "__")
        dest = ws / flat
        mark = "  "
        if not dest.exists():
            shutil.copyfile(Path(args.corpus) / doc.doc_id, dest)
            new, mark = new + 1, "+ "
        text = preview(doc.text, args.query)
        print(f"{mark}{rank:>2}. [{score:5.1f}] {flat}\n      {text}")
    total = sum(1 for _ in ws.iterdir())
    print(f"\n새로 추가 {new}개, workspace 문서 {total}개 ({ws})")


if __name__ == "__main__":
    main()

"""LLM 없이 검색 단계만 비교한다: RAG(BM25 청크 top-k)와 DR-DCI pull(BM25 문서 top-k).

각 질문에 대해 다음을 잰다.
- 문서 재현율: 정답 문서가 검색 결과 안에 있는가
- 정답 청크 재현율(RAG만): 정답 문장이 든 청크가 top-k 안에 있는가. RAG는 이 청크만 LLM에 넘기므로 이게 실제 성패다.
- 컨텍스트 크기: LLM에 넘어가는 글자 수

예: python agentic-search/eval_retrieval.py --k 5
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from corpus_tools import BM25, chunk_docs, load_corpus


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--corpus", default="data/corpus")
    ap.add_argument("--questions", default="agentic-search/questions.json")
    ap.add_argument("--k", type=int, default=5, help="RAG 청크 top-k")
    ap.add_argument("--pull-k", type=int, default=8, help="DR-DCI pull 문서 top-k")
    ap.add_argument("--chunk", type=int, default=1000)
    ap.add_argument("--out", default="outputs/eval_retrieval.json")
    args = ap.parse_args()

    docs = load_corpus(Path(args.corpus))
    chunks = chunk_docs(docs, size=args.chunk)
    qs = json.loads(Path(args.questions).read_text(encoding="utf-8"))["questions"]
    print(
        f"문서 {len(docs)}개, 청크 {len(chunks)}개 ({args.chunk}자), 질문 {len(qs)}개\n"
    )

    rows, summary = [], {}
    for mode in ("space", "bigram"):
        doc_index, chunk_index = BM25(docs, mode), BM25(chunks, mode)
        hits = {"rag_doc": 0, "rag_answer_chunk": 0, "pull_doc": 0}
        ctx = 0
        for q in qs:
            gold, rx = set(q["gold_files"]), re.compile(q["answer_regex"], re.MULTILINE)
            top = chunk_index.search(q["q"], args.k)
            rag_doc = any(c.doc_id.split("#")[0] in gold for _, c in top)
            rag_ans = any(
                c.doc_id.split("#")[0] in gold and rx.search(c.text) for _, c in top
            )
            pulled = [d.doc_id for _, d in doc_index.search(q["q"], args.pull_k)]
            pull_doc = bool(gold & set(pulled))
            used = sum(len(c.text) for _, c in top)
            ctx += used
            hits["rag_doc"] += rag_doc
            hits["rag_answer_chunk"] += rag_ans
            hits["pull_doc"] += pull_doc
            rows.append(
                {
                    "tokenizer": mode,
                    "id": q["id"],
                    "rag_doc": rag_doc,
                    "rag_answer_chunk": rag_ans,
                    "pull_doc": pull_doc,
                    "pull_rank": next(
                        (i + 1 for i, p in enumerate(pulled) if p in gold), None
                    ),
                    "rag_context_chars": used,
                }
            )
        n = len(qs)
        summary[mode] = {k: f"{v}/{n}" for k, v in hits.items()} | {
            "rag_context_chars_avg": ctx // n
        }
        print(
            f"[{mode:6}] RAG 문서 {hits['rag_doc']}/{n} | RAG 정답청크 {hits['rag_answer_chunk']}/{n} | "
            f"pull 문서(top{args.pull_k}) {hits['pull_doc']}/{n} | RAG 컨텍스트 평균 {ctx // n:,}자"
        )

    print("\n질문별 (bigram): id  RAG정답청크  pull순위")
    for r in rows:
        if r["tokenizer"] == "bigram":
            print(
                f"  {r['id']}  {'O' if r['rag_answer_chunk'] else 'X'}  {r['pull_rank']}"
            )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"args": vars(args), "summary": summary, "rows": rows},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

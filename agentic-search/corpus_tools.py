"""코퍼스 읽기, 한국어 토크나이저, BM25. 다른 스크립트가 공용으로 쓴다.

외부 의존성 없이 표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

HANGUL = re.compile(r"[가-힣]")
WORD = re.compile(r"[0-9A-Za-z_\-\.\$/@]+|[가-힣]+")


def tokenize(text: str, mode: str = "bigram") -> list[str]:
    """mode="space": 공백/기호 기준 단어. 조사가 붙은 한국어("스킬을")는 "스킬"과 다른 토큰이 된다.
    mode="bigram": 한글 단어는 2글자 조각으로 쪼갠다("스킬을" -> 스킬, 킬을). 조사 문제를 줄인다.
    """
    words = [w.lower().strip(".-/") for w in WORD.findall(text)]
    words = [w for w in words if w]
    if mode == "space":
        return words
    out: list[str] = []
    for w in words:
        if HANGUL.search(w) and len(w) > 1:
            out.extend(w[i : i + 2] for i in range(len(w) - 1))
        else:
            out.append(w)
    return out


@dataclass
class Doc:
    doc_id: str  # 코퍼스 폴더 기준 상대 경로
    text: str


def load_corpus(corpus_dir: Path) -> list[Doc]:
    files = sorted(p for p in corpus_dir.rglob("*.md") if p.is_file())
    return [
        Doc(
            str(p.relative_to(corpus_dir)),
            p.read_text(encoding="utf-8", errors="replace"),
        )
        for p in files
    ]


def chunk_docs(docs: list[Doc], size: int = 1000, overlap: int = 200) -> list[Doc]:
    """RAG 기준선용: 문서를 글자 수 기준으로 겹치게 자른다. doc_id 뒤에 #번호를 붙인다."""
    chunks: list[Doc] = []
    step = size - overlap
    for d in docs:
        for n, start in enumerate(range(0, max(len(d.text) - overlap, 1), step)):
            chunks.append(Doc(f"{d.doc_id}#{n}", d.text[start : start + size]))
    return chunks


class BM25:
    def __init__(
        self, docs: list[Doc], mode: str = "bigram", k1: float = 1.5, b: float = 0.75
    ):
        self.docs, self.mode, self.k1, self.b = docs, mode, k1, b
        self.tfs = [Counter(tokenize(d.text, mode)) for d in docs]
        self.lens = [sum(tf.values()) for tf in self.tfs]
        self.avg = sum(self.lens) / max(len(self.lens), 1)
        df: Counter = Counter()
        for tf in self.tfs:
            df.update(tf.keys())
        n = len(docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def search(self, query: str, k: int = 10) -> list[tuple[float, Doc]]:
        q = [t for t in tokenize(query, self.mode) if t in self.idf]
        scored = []
        for i, tf in enumerate(self.tfs):
            s = 0.0
            norm = self.k1 * (1 - self.b + self.b * self.lens[i] / self.avg)
            for t in q:
                f = tf.get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + norm)
            if s > 0:
                scored.append((s, self.docs[i]))
        scored.sort(key=lambda x: -x[0])
        return scored[:k]

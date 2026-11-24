"""공부 자료 저장소의 한국어 문서를 모아 DCI용 코퍼스 폴더를 만든다.

코퍼스 = 문서 하나당 파일 하나인 평범한 폴더. 인덱스도 벡터 DB도 만들지 않는다(DCI 논문과 같은 형태).

예:
  git clone --depth 1 https://github.com/luongnv89/claude-howto ../_src/claude-howto
  git clone --depth 1 https://github.com/walkinglabs/learn-harness-engineering ../_src/harness
  python agentic-search/build_corpus.py \
      --src howto=../_src/claude-howto/ko --src harness=../_src/harness/docs/ko
결과는 data/corpus/ 에 생긴다(.gitignore 대상, 커밋하지 않음). 두 저장소 모두 MIT 라이선스.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--src", action="append", required=True, help="이름=폴더 (여러 번 지정 가능)"
    )
    ap.add_argument("--out", default="data/corpus", help="코퍼스를 만들 폴더")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    total_files = total_chars = 0
    for spec in args.src:
        name, _, folder = spec.partition("=")
        src = Path(folder)
        for p in sorted(src.rglob("*.md")):
            dest = out / name / p.relative_to(src)
            dest.parent.mkdir(parents=True, exist_ok=True)
            text = p.read_text(encoding="utf-8", errors="replace")
            dest.write_text(text, encoding="utf-8")
            total_files += 1
            total_chars += len(text)
    print(f"{out}: 문서 {total_files}개, {total_chars:,}자")


if __name__ == "__main__":
    main()

"""지시 파일 로딩 방식 3가지를 작업별로 비교한다.

A. monolith    : 모든 규칙을 CLAUDE.md 한 파일에 넣는다. 매 작업마다 전부 읽힌다.
B. entry+links : 짧은 입구 파일 + 주제 문서. 에이전트가 필요한 문서만 골라 읽는다고 가정한다.
C. entry+rules : 짧은 입구 파일 + `paths:` 프런트매터가 있는 규칙 파일.
                 작업이 건드린 파일 경로와 맞는 규칙만 자동으로 읽힌다.

측정 항목: 작업마다 컨텍스트에 들어간 지시 토큰, 그중 그 작업에 필요한 비율(신호 대 잡음),
빠진 규칙 수, 그리고 월간 비용 추정.

사용 예:
    python harness-lab/01-instructions/measure_instructions.py
    python harness-lab/01-instructions/measure_instructions.py --counter claude --model claude-opus-5-5
    python harness-lab/01-instructions/measure_instructions.py --check

--counter approx (기본) 는 API를 부르지 않는 근사치다.
--counter claude 는 Anthropic count_tokens 엔드포인트로 정확히 센다(텍스트 생성은 하지 않음).
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
MAX_ENTRY_LINES = 200
MAX_HARD_RULES = 15


@dataclass
class Rule:
    name: str
    paths: list[str]
    body: str


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """`paths:` 프런트매터를 읽어 (글롭 목록, 본문)을 돌려준다."""
    if not text.startswith("---\n"):
        return [], text
    end = text.index("\n---\n", 4)
    header, body = text[4:end], text[end + 5 :]
    paths = re.findall(r'^\s*-\s*"([^"]+)"', header, flags=re.MULTILINE)
    return paths, body


def glob_to_regex(glob: str) -> re.Pattern[str]:
    """`**/` 는 0개 이상의 폴더, `*` 는 한 폴더 안의 아무 글자."""
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif glob.startswith("**", i):
            out, i = out + ".*", i + 2
        elif glob[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    return re.compile(out + r"\Z")


def rule_matches(rule: Rule, touched: list[str]) -> bool:
    return any(glob_to_regex(g).match(f) for g in rule.paths for f in touched)


def load_layout(root: Path) -> tuple[str, list[Rule]]:
    entry = (root / "CLAUDE.md").read_text(encoding="utf-8")
    rules = []
    for p in sorted((root / "rules").glob("*.md")):
        paths, body = split_frontmatter(p.read_text(encoding="utf-8"))
        rules.append(Rule(p.stem, paths, body))
    return entry, rules


def build_monolith(entry: str, rules: list[Rule]) -> str:
    """입구 파일의 '주제 문서' 목차를 빼고 규칙 본문을 전부 이어 붙인다 (내용은 같게)."""
    head = entry.split("## 주제 문서")[0].rstrip()
    return head + "\n\n" + "\n\n".join(r.body.strip() for r in rules) + "\n"


class ApproxCounter:
    """API 없이 쓰는 근사치: 한글 등 비ASCII 글자 1자 = 1토큰, ASCII 4자 = 1토큰."""

    label = "approx (근사치)"

    def count(self, text: str) -> int:
        non_ascii = sum(1 for ch in text if ord(ch) > 127)
        ascii_chars = len(text) - non_ascii
        return non_ascii + (ascii_chars + 3) // 4


class ClaudeCounter:
    """Anthropic count_tokens 엔드포인트. ANTHROPIC_API_KEY 등 인증이 필요하다."""

    def __init__(self, model: str) -> None:
        from anthropic import Anthropic

        self.client = Anthropic()
        self.model = model
        self.label = f"claude count_tokens ({model})"
        self._base = self._raw("x")

    def _raw(self, text: str) -> int:
        resp = self.client.messages.count_tokens(
            model=self.model, messages=[{"role": "user", "content": text}]
        )
        return resp.input_tokens

    def count(self, text: str) -> int:
        # 메시지 포장에 드는 고정 토큰을 빼서 텍스트 자체의 토큰만 남긴다.
        return max(0, self._raw(text) - self._base + 1)


def measure(counter, entry: str, rules: list[Rule], tasks: list[dict]) -> list[dict]:
    monolith = build_monolith(entry, rules)
    tok_entry = counter.count(entry)
    tok_mono = counter.count(monolith)
    tok_rule = {r.name: counter.count(r.body) for r in rules}
    rows = []
    for t in tasks:
        needed = set(t["needs"])
        relevant = tok_entry + sum(tok_rule[n] for n in needed)
        loaded_c = {r.name for r in rules if rule_matches(r, t["touched"])}
        strategies = {
            "A monolith": (tok_mono, set(tok_rule)),
            "B entry+links": (tok_entry + sum(tok_rule[n] for n in needed), needed),
            "C entry+rules": (tok_entry + sum(tok_rule[n] for n in loaded_c), loaded_c),
        }
        for name, (loaded, docs) in strategies.items():
            rows.append(
                {
                    "task": t["id"],
                    "task_name": t["name"],
                    "strategy": name,
                    "loaded": loaded,
                    "snr": min(1.0, relevant / loaded),
                    "missing": sorted(needed - docs),
                    "extra": sorted(docs - needed),
                }
            )
    return rows


def print_report(rows, counter_label, sessions, turns, price_in, price_cache_read):
    print(f"토큰 계산: {counter_label}\n")
    print(
        f"{'작업':<24}{'방식':<16}{'지시 토큰':>10}{'SNR':>7}  빠진 규칙 / 불필요하게 읽힌 규칙"
    )
    for r in rows:
        miss = ",".join(r["missing"]) or "-"
        extra = ",".join(r["extra"]) or "-"
        print(
            f"{r['task'] + ' ' + r['task_name']:<24}{r['strategy']:<16}"
            f"{r['loaded']:>10,}{r['snr']:>7.0%}  {miss} / {extra}"
        )
    print("\n방식별 평균 (작업 5개)")
    base = None
    for s in ["A monolith", "B entry+links", "C entry+rules"]:
        sel = [r for r in rows if r["strategy"] == s]
        avg = sum(r["loaded"] for r in sel) / len(sel)
        snr = sum(r["snr"] for r in sel) / len(sel)
        miss = sum(len(r["missing"]) for r in sel)
        base = base or avg
        # 세션 첫 턴은 캐시 쓰기(입력 단가 x1.25), 이후 턴은 캐시 읽기 단가로 계산한다.
        per_session = avg * (1.25 * price_in + (turns - 1) * price_cache_read) / 1e6
        print(
            f"  {s:<16} 평균 {avg:>7,.0f} 토큰  (A 대비 {avg / base:>5.0%})  SNR {snr:>4.0%}  "
            f"빠진 규칙 {miss}건  월 {sessions}세션 지시 비용 ${per_session * sessions:,.2f}"
        )


def check_layout(root: Path) -> int:
    entry, rules = load_layout(root)
    problems = []
    lines = entry.count("\n") + 1
    hard = re.search(r"## 강제 규칙.*?\n(.*?)(?:\n## |\Z)", entry, flags=re.DOTALL)
    n_hard = (
        len(re.findall(r"^\d+\.", hard.group(1), flags=re.MULTILINE)) if hard else 0
    )
    if lines > MAX_ENTRY_LINES:
        problems.append(f"입구 파일이 {lines}줄 (기준 {MAX_ENTRY_LINES}줄 이하)")
    if n_hard > MAX_HARD_RULES:
        problems.append(f"강제 규칙 {n_hard}개 (기준 {MAX_HARD_RULES}개 이하)")
    for link in re.findall(r"`(rules/[^`]+\.md)`", entry):
        if not (root / link).exists():
            problems.append(f"입구 파일의 링크가 없는 파일을 가리킴: {link}")
    seen: dict[str, str] = {}
    for r in rules:
        if not r.paths:
            problems.append(f"{r.name}.md 에 paths 가 없음 (항상 읽힘)")
        for line in r.body.splitlines():
            key = line.strip()
            if key.startswith("- ") and len(key) > 20:
                if key in seen:
                    problems.append(f"같은 규칙이 두 곳에 있음: {seen[key]} / {r.name}")
                seen[key] = r.name
    print(f"입구 파일 {lines}줄, 강제 규칙 {n_hard}개, 규칙 파일 {len(rules)}개")
    for p in problems:
        print(f"  문제: {p}")
    print("결과:", "통과" if not problems else f"문제 {len(problems)}건")
    return 1 if problems else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--layout", type=Path, default=FIXTURES / "split")
    ap.add_argument("--tasks", type=Path, default=FIXTURES / "tasks.json")
    ap.add_argument("--counter", choices=["approx", "claude"], default="approx")
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument(
        "--seed",
        type=int,
        default=0,
        help="작업 순서를 섞는 시드 (결과 값에는 영향 없음)",
    )
    ap.add_argument("--sessions", type=int, default=100, help="한 달 세션 수")
    ap.add_argument("--turns", type=int, default=20, help="세션당 턴 수")
    ap.add_argument("--price-in", type=float, default=4.0, help="입력 1M 토큰당 달러")
    ap.add_argument(
        "--price-cache-read", type=float, default=0.20, help="캐시 읽기 1M 토큰당 달러"
    )
    ap.add_argument(
        "--check", action="store_true", help="입구 파일과 규칙 파일 점검만 한다"
    )
    ap.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    args = ap.parse_args()

    if args.check:
        raise SystemExit(check_layout(args.layout))

    random.seed(args.seed)
    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
    random.shuffle(tasks)
    tasks.sort(key=lambda t: t["id"])
    entry, rules = load_layout(args.layout)
    counter = ApproxCounter() if args.counter == "approx" else ClaudeCounter(args.model)
    rows = measure(counter, entry, rules, tasks)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    print_report(
        rows,
        counter.label,
        args.sessions,
        args.turns,
        args.price_in,
        args.price_cache_read,
    )


if __name__ == "__main__":
    main()

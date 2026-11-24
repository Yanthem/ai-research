---
name: code-review-specialist
description: Review code or a PR in this repo for security, correctness, performance and maintainability, and report findings by severity. Use when asked to review code, a diff or a pull request.
---

# Code Review

Review the code the user points to (file, diff or PR). This repo is mostly Python 3.11+ experiment scripts; follow CLAUDE.md (ruff, argparse with seed and model name exposed, no hardcoded API keys).

## Check, in this order

1. **Security**: hardcoded secrets or API keys, unvalidated input, injection (SQL, shell, `eval`), secrets in logs.
2. **Correctness**: wrong logic, unhandled errors, edge cases (empty input, None, off-by-one), unchecked API responses.
3. **Performance**: O(n²) loops, repeated work that could be cached, needless API calls or tokens, blocking I/O in loops.
4. **Maintainability**: functions over ~50 lines, unclear names, duplicated code, missing type hints on public functions.
5. **Reproducibility** (experiment scripts): seed fixed and exposed, model ID as an argument, results logged with date and hyperparameters, dependencies pinned.
6. **Tests**: are the changed paths tested, are edge and error cases covered.

## Optional metrics

- `python .claude/skills/code-review-specialist/scripts/analyze-metrics.py <file>`: rough counts (functions, classes, complexity score).
- `python .claude/skills/code-review-specialist/scripts/compare-complexity.py <before> <after>`: use only when reviewing a refactor.

Both are regex-based estimates for Python. Quote them as rough numbers, not as facts.

## Report format

1. **Summary**: overall quality 1-5, number of findings per severity, the one area to fix first.
2. **Findings**, most severe first. For each: severity (Critical / High / Medium / Low), `file:line`, what is wrong, why it matters, and a short fix (code when it helps).
3. Leave out empty categories. If nothing is wrong, say so in one line.

"""
crew_mcp.py — Claude Code에서 로컬 Qwen(Ollama)과 GPT(API)를 부르는 MCP 서버.

외부 패키지 없이 Python 표준 라이브러리만 쓴다 (pip install 필요 없음).

Claude Code가 이 파일을 실행해 두고, 필요할 때 아래 도구를 부른다.
  qwen         : Qwen에게 질문. files를 주면 서버가 직접 파일을 읽어 붙인다
                 (Claude가 파일 내용을 옮기지 않으므로 Claude 토큰이 절약된다).
  qwen_git     : git fetch/pull/status/diff 를 실행하고 Qwen이 요약·리뷰한다.
  qwen_run     : 테스트·린트 같은 명령을 실행하고, 긴 로그를 Qwen이 요약한다.
  gpt          : OpenAI API로 GPT에게 묻는다. .crew/CONTEXT.md(공유 컨텍스트)를 자동으로 붙인다.
                 (Codex CLI를 쓰면 이 도구 대신 codex MCP를 쓴다. README 참고)

점검:  python orchestra/crew_mcp.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "qwen3.5:9b")
QWEN_CTX = int(os.environ.get("QWEN_CTX", "16384"))
QWEN_THINK = os.environ.get("QWEN_THINK", "false").lower() == "true"
GPT_MODEL = os.environ.get("GPT_MODEL", "gpt-5")
SEED = int(os.environ.get("CREW_SEED", "42"))
ROOT = Path(os.environ.get("CREW_ROOT", os.getcwd())).resolve()
CONTEXT_FILE = ROOT / ".crew" / "CONTEXT.md"

MAX_FILE_CHARS = 40_000  # 파일 하나당 최대 글자 수 (Qwen 컨텍스트 보호)
MAX_LOG_CHARS = 30_000  # 명령 출력 최대 글자 수
TAIL_CHARS = 1_500  # Claude에게 그대로 돌려주는 로그 끝부분 길이

QWEN_SYSTEM = (
    "You are a fast local assistant doing simple, repetitive checks for a lead engineer (Claude). "
    "Be short and concrete. Use bullet points. Answer in Korean unless asked otherwise. "
    "If you are not sure, say so instead of guessing."
)


# ---------------------------------------------------------------- helpers
def _post_json(
    url: str, payload: dict, headers: dict | None = None, timeout: int = 600
) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", **(headers or {})}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _read_files(files: list[str] | None) -> str:
    parts = []
    for f in files or []:
        p = (ROOT / f).resolve()
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            parts.append(f"### {f}\n(읽기 실패: {e})")
            continue
        if len(text) > MAX_FILE_CHARS:
            text = text[:MAX_FILE_CHARS] + "\n...(잘림)"
        parts.append(f"### {f}\n```\n{text}\n```")
    return "\n\n".join(parts)


def _run(cmd: str, timeout: int = 600) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            cwd=ROOT,
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, f"(시간 초과 {timeout}초: {cmd})"


def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else "...(앞부분 생략)\n" + text[-n:]


def ask_qwen(prompt: str, system: str = QWEN_SYSTEM) -> str:
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "think": QWEN_THINK,
        "options": {"num_ctx": QWEN_CTX, "temperature": 0.2, "seed": SEED},
    }
    try:
        out = _post_json(f"{OLLAMA_URL}/api/chat", payload)
    except urllib.error.HTTPError as e:
        if e.code == 400:  # 일부 모델/버전은 think 옵션을 거부한다 -> 빼고 재시도
            payload.pop("think", None)
            out = _post_json(f"{OLLAMA_URL}/api/chat", payload)
        else:
            raise
    except urllib.error.URLError as e:
        return f"[Qwen 연결 실패] Ollama가 켜져 있는지 확인하세요 ({OLLAMA_URL}): {e}"
    return out.get("message", {}).get("content", "").strip() or "(빈 응답)"


def ask_gpt(prompt: str) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return "[GPT 사용 불가] OPENAI_API_KEY가 없습니다. Codex CLI를 쓰는 경우 codex MCP 도구를 쓰세요."
    payload = {
        "model": GPT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "reasoning_effort": "low",
    }
    try:
        out = _post_json(
            "https://api.openai.com/v1/chat/completions",
            payload,
            headers={"Authorization": f"Bearer {key}"},
        )
    except urllib.error.HTTPError as e:
        return f"[GPT 오류 {e.code}] {e.read().decode('utf-8', 'replace')[:500]}"
    u = out.get("usage", {})
    text = out["choices"][0]["message"]["content"]
    return f"{text}\n\n(GPT 토큰: 입력 {u.get('prompt_tokens')} / 출력 {u.get('completion_tokens')})"


# ---------------------------------------------------------------- tools
def tool_qwen(prompt: str, files: list[str] | None = None) -> str:
    body = prompt
    if files:
        body += "\n\n" + _read_files(files)
    return ask_qwen(body)


def tool_qwen_git(action: str = "review", base: str = "HEAD") -> str:
    """action: status | pull | review"""
    if action == "pull":
        code, out = _run("git pull --ff-only")
        _, log = _run("git log --oneline -15")
        summary = ask_qwen(
            f"git pull 결과와 최근 커밋이다. 무엇이 바뀌었는지 3줄로 요약해.\n\n{out}\n\n{log}"
        )
        return f"[git pull 종료코드 {code}]\n{_clip(out, TAIL_CHARS)}\n\n[Qwen 요약]\n{summary}"
    _run("git fetch --quiet")
    _, status = _run("git status -sb")
    if action == "status":
        return status
    _, stat = _run(f"git diff {base} --stat")
    _, diff = _run(f"git diff {base}")
    if not diff.strip():
        return f"{status}\n변경 사항이 없습니다."
    review = ask_qwen(
        "아래 git diff를 리뷰해. 다음만 짧게 짚어: (1) 명백한 버그·오타 (2) 디버그용 print/하드코딩된 키·경로 "
        "(3) 빠진 import나 깨질 만한 부분. 문제가 없으면 '문제 없음'이라고만 써.\n\n"
        + _clip(diff, MAX_LOG_CHARS)
    )
    return f"{status}\n{stat}\n[Qwen 리뷰]\n{review}"


def tool_qwen_run(command: str, question: str = "") -> str:
    code, out = _run(command)
    ask = (
        question
        or "실패한 항목과 원인, 고칠 위치(파일:줄)만 짧게 정리해. 모두 통과했으면 '통과'라고만 써."
    )
    summary = ask_qwen(
        f"명령: {command}\n종료코드: {code}\n\n{ask}\n\n출력:\n{_clip(out, MAX_LOG_CHARS)}"
    )
    return f"[종료코드 {code}]\n[Qwen 요약]\n{summary}\n\n[출력 끝부분]\n{_clip(out, TAIL_CHARS)}"


def tool_gpt(
    prompt: str, files: list[str] | None = None, include_context: bool = True
) -> str:
    body = ""
    if include_context and CONTEXT_FILE.exists():
        body += (
            "## 공유 컨텍스트 (.crew/CONTEXT.md)\n"
            + CONTEXT_FILE.read_text(encoding="utf-8")
            + "\n\n"
        )
    body += "## 요청\n" + prompt
    if files:
        body += "\n\n" + _read_files(files)
    return ask_gpt(body)


STR_LIST = {"type": "array", "items": {"type": "string"}}
TOOLS = {
    "qwen": (
        tool_qwen,
        (
            "로컬 Qwen에게 단순·반복 작업을 맡긴다(요약, 형식 변환, 간단 리뷰, 체크리스트 대조). "
            "files에 프로젝트 기준 상대 경로를 주면 서버가 직접 읽어 붙인다. 복잡한 추론에는 쓰지 말 것."
        ),
        {"prompt": {"type": "string"}, "files": STR_LIST},
        ["prompt"],
    ),
    "qwen_git": (
        tool_qwen_git,
        "git 작업. action=status(상태), pull(git pull --ff-only 후 요약), review(base 대비 diff를 Qwen이 리뷰).",
        {
            "action": {"type": "string", "enum": ["status", "pull", "review"]},
            "base": {"type": "string"},
        },
        [],
    ),
    "qwen_run": (
        tool_qwen_run,
        "테스트·린트·빌드 명령을 프로젝트 폴더에서 실행하고, 긴 출력을 Qwen이 요약해 돌려준다.",
        {"command": {"type": "string"}, "question": {"type": "string"}},
        ["command"],
    ),
    "gpt": (
        tool_gpt,
        "OpenAI API로 GPT에게 교차 확인을 요청한다. .crew/CONTEXT.md를 자동으로 붙인다. OPENAI_API_KEY 필요.",
        {
            "prompt": {"type": "string"},
            "files": STR_LIST,
            "include_context": {"type": "boolean"},
        },
        ["prompt"],
    ),
}


# ---------------------------------------------------------------- MCP (stdio JSON-RPC)
def _send(msg: dict) -> None:
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def serve() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid, method = req.get("id"), req.get("method", "")
        if rid is None:  # notification (예: notifications/initialized)
            continue
        params = req.get("params") or {}
        if method == "initialize":
            result = {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "crew", "version": "1.0.0"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": name,
                        "description": desc,
                        "inputSchema": {
                            "type": "object",
                            "properties": props,
                            "required": req_,
                        },
                    }
                    for name, (_, desc, props, req_) in TOOLS.items()
                ]
            }
        elif method == "tools/call":
            name, args = params.get("name"), params.get("arguments") or {}
            try:
                text = TOOLS[name][0](**args)
                result = {"content": [{"type": "text", "text": text}]}
            except Exception as e:  # noqa: BLE001 도구 오류는 Claude가 읽을 수 있게 돌려준다
                result = {
                    "content": [
                        {"type": "text", "text": f"[오류] {type(e).__name__}: {e}"}
                    ],
                    "isError": True,
                }
        elif method == "ping":
            result = {}
        else:
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": rid,
                    "error": {"code": -32601, "message": f"unknown method {method}"},
                }
            )
            continue
        _send({"jsonrpc": "2.0", "id": rid, "result": result})


def check() -> None:
    print(f"프로젝트 폴더: {ROOT}")
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as r:
            names = [m["name"] for m in json.loads(r.read())["models"]]
        ok = QWEN_MODEL in names
        print(
            f"[{'OK' if ok else '주의'}] Ollama 연결됨. 설치된 모델: {', '.join(names) or '(없음)'}"
        )
        if not ok:
            print(
                f"       '{QWEN_MODEL}'이 없습니다. ollama pull {QWEN_MODEL} 또는 QWEN_MODEL 환경 변수를 위 이름으로 설정"
            )
        else:
            print("       Qwen 응답 시험:", ask_qwen("'준비 완료'라고만 답해.")[:80])
    except Exception as e:  # noqa: BLE001
        print(
            f"[실패] Ollama 연결 안 됨 ({OLLAMA_URL}): {e}  -> 'ollama serve' 실행 또는 Ollama 앱 켜기"
        )
    print(
        f"[{'OK' if shutil.which('codex') else '없음'}] Codex CLI (GPT를 구독으로 쓰는 방법)"
    )
    print(
        f"[{'OK' if os.environ.get('OPENAI_API_KEY') else '없음'}] OPENAI_API_KEY (GPT를 API로 쓰는 방법)"
    )
    print(f"[{'OK' if shutil.which('git') else '없음'}] git")
    print(
        "Codex CLI나 OPENAI_API_KEY 둘 중 하나만 있으면 GPT 교차 확인을 쓸 수 있습니다."
    )


def main() -> None:
    global QWEN_MODEL, GPT_MODEL, SEED
    ap = argparse.ArgumentParser(description="Claude Code용 Qwen/GPT MCP 서버")
    ap.add_argument("--check", action="store_true", help="연결 상태 점검만 하고 끝낸다")
    ap.add_argument("--qwen-model", default=QWEN_MODEL)
    ap.add_argument("--gpt-model", default=GPT_MODEL)
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args()
    QWEN_MODEL, GPT_MODEL, SEED = a.qwen_model, a.gpt_model, a.seed
    check() if a.check else serve()


if __name__ == "__main__":
    main()

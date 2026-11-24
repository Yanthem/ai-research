# 이 저장소의 팀 구성(커맨드, 서브에이전트, MCP 서버)을 "내 PC 전체"에서 쓰도록 설치한다.
# 대회용 폴더처럼 ai-research가 아닌 다른 폴더에서도 /team-plan 등을 쓰려면 한 번 실행한다.
# 실행: 저장소 폴더에서  powershell -ExecutionPolicy Bypass -File orchestra\install_user.ps1

$repo = Split-Path -Parent $PSScriptRoot
$userClaude = Join-Path $env:USERPROFILE ".claude"
New-Item -ItemType Directory -Force -Path "$userClaude\commands", "$userClaude\agents" | Out-Null

foreach ($f in "team-plan.md", "xcheck.md", "qcheck.md", "sync.md") {
    Copy-Item "$repo\.claude\commands\$f" "$userClaude\commands\$f" -Force
}
foreach ($f in "qwen-worker.md") {
    Copy-Item "$repo\.claude\agents\$f" "$userClaude\agents\$f" -Force
}
Write-Host "커맨드 4개, 서브에이전트 1개를 $userClaude 에 복사했습니다."

# MCP 서버를 user 범위로 등록 (이미 있으면 지우고 다시 등록)
$server = Join-Path $repo "orchestra\crew_mcp.py"
claude mcp remove crew --scope user 2>$null | Out-Null
claude mcp add crew --scope user -e QWEN_MODEL=qwen3.5:9b -- python "$server"
# 예전 버전이 등록한 codex MCP(codex mcp-server)는 Codex 0.154.0에서 없어졌으므로 지운다
claude mcp remove codex --scope user 2>$null | Out-Null
# 역할 규칙을 모든 폴더에서 적용: ~/.claude/CLAUDE.md 에 import 한 줄 추가
Copy-Item "$repo\orchestra\CLAUDE.crew.md" "$userClaude\CLAUDE.crew.md" -Force
$userMd = Join-Path $userClaude "CLAUDE.md"
$line = "@~/.claude/CLAUDE.crew.md"
if (-not (Test-Path $userMd) -or -not (Select-String -Path $userMd -SimpleMatch $line -Quiet)) {
    Add-Content -Path $userMd -Value "`n$line" -Encoding utf8
}
Write-Host "역할 규칙(CLAUDE.crew.md)을 모든 폴더에 적용했습니다."
Write-Host ""
Write-Host "완료. 새 폴더에서 'claude' 실행 후 /mcp 로 crew와 reason-network가 connected인지 확인하세요."

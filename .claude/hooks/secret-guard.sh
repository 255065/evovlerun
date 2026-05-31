#!/bin/bash
# PreToolUse hook for Edit|Write. Always on. Blocks writes to secret-bearing
# files so no agent (or the orchestrator) can ever create/modify them. Sits
# alongside the git pre-commit hook, which catches the manual `git commit` path.
#
# Exit 0 = allow, exit 2 = block (stderr shown to the model).

set -euo pipefail

INPUT="$(cat)"
FILE_PATH="$(printf '%s' "$INPUT" | python3 -c 'import sys,json
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")' 2>/dev/null || true)"

[ -z "$FILE_PATH" ] && exit 0

BASE="$(basename "$FILE_PATH")"

# Allow example/template env files — they carry no real secrets.
case "$BASE" in
  *.example|*.sample|*.template) exit 0 ;;
esac

deny() {
  echo "secret-guard: refusing to write secret-bearing file '$BASE'." >&2
  echo "Secrets belong in environment variables (Railway / Vercel), never in the repo." >&2
  exit 2
}

case "$BASE" in
  .env|.env.*) deny ;;
  *.key|*.pem|*.p12|*.pfx) deny ;;
  secrets.json|credentials.json|service-account*.json) deny ;;
  *) exit 0 ;;
esac

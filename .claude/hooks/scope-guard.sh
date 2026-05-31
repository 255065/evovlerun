#!/bin/bash
# PreToolUse hook for Edit|Write. Enforces the feature-factory scope sentinel:
# when an agent is "scoped" to backend/frontend/tests, block writes outside it.
#
# Fail-open by design: if there is no sentinel file, allow everything. That way
# normal (non-factory) sessions are never restricted — the guard only bites
# while the orchestrator has set an active scope.
#
# Protocol: read PreToolUse JSON on stdin, exit 0 to allow, exit 2 to block
# (stderr is shown back to the model).

set -euo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
SENTINEL="$ROOT/.claude/.active-scope"

# No active scope → not in a factory run → allow.
[ -f "$SENTINEL" ] || exit 0

SCOPE="$(tr -d '[:space:]' < "$SENTINEL")"
[ -z "$SCOPE" ] && exit 0

INPUT="$(cat)"
FILE_PATH="$(printf '%s' "$INPUT" | python3 -c 'import sys,json
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")' 2>/dev/null || true)"

# No file path in the tool input → nothing to guard.
[ -z "$FILE_PATH" ] && exit 0

# Normalize to a repo-relative path when possible.
case "$FILE_PATH" in
  "$ROOT"/*) REL="${FILE_PATH#"$ROOT"/}" ;;
  *)         REL="$FILE_PATH" ;;
esac

deny() {
  echo "scope-guard: active scope is '$SCOPE' — this agent may not write '$REL'." >&2
  echo "If this edit is legitimate, it belongs to a different builder. Surface it as feedback instead of writing here." >&2
  exit 2
}

case "$SCOPE" in
  backend)
    case "$REL" in
      backend/*|supabase/migrations/*) exit 0 ;;
      *) deny ;;
    esac
    ;;
  frontend)
    case "$REL" in
      frontend/*) exit 0 ;;
      *) deny ;;
    esac
    ;;
  tests)
    # Test Verifier: test files only, either stack.
    case "$REL" in
      backend/tests/*|*test_*.py|*_test.py) exit 0 ;;
      *.test.ts|*.test.tsx|*.spec.ts|*.spec.tsx|*__tests__*) exit 0 ;;
      *) deny ;;
    esac
    ;;
  readonly)
    deny
    ;;
  *)
    # Unknown scope value → fail open rather than block legitimate work.
    exit 0
    ;;
esac

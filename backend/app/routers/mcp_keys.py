"""MCP API key management.

A user generates a key here, pastes it into Claude Desktop / ChatGPT, and the
MCP server uses it to identify them on every tool call. We store only a SHA-256
hash of the key so a database breach can't be turned into impersonation.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.security import CurrentUser, get_current_user
from app.core.supabase import get_supabase_admin

router = APIRouter(prefix="/mcp-keys", tags=["mcp-keys"])

KEY_PREFIX = "evr_"  # so users can recognize them on sight


def _mcp_url() -> str:
    """Public URL of the hosted MCP endpoint clients connect to."""
    base = os.environ.get("MCP_PUBLIC_URL") or get_settings().backend_public_url
    return base.rstrip("/") + "/mcp"


class CreateKeyBody(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class InstallSnippets(BaseModel):
    """All the install material a freshly-generated key needs.

    Shown to the user once after creation. After they navigate away the raw
    key is gone — we only kept its hash.
    """
    claude_desktop_config_snippet: str
    macos_install_script: str
    mcp_url: str
    claude_config_file_path: str


class CreateKeyReply(BaseModel):
    id: str
    name: str
    key: str  # full key — returned ONCE
    key_prefix: str
    created_at: datetime
    install: InstallSnippets


def _build_install_snippets(api_key: str) -> InstallSnippets:
    """Render the pre-filled config + bash auto-installer for this API key.

    Hosted MCP: the client connects to our remote server over HTTP via the
    `mcp-remote` npm shim (no repo clone, works on any machine). The key is
    passed as a Bearer header. The install script patches Claude Desktop's
    config file and restarts the app — no JSON editing.
    """
    url = _mcp_url()
    claude_cfg = "$HOME/Library/Application Support/Claude/claude_desktop_config.json"

    config_snippet = (
        '{\n'
        '  "mcpServers": {\n'
        '    "evolverun": {\n'
        '      "command": "npx",\n'
        '      "args": [\n'
        '        "-y",\n'
        '        "mcp-remote",\n'
        f'        "{url}",\n'
        '        "--header",\n'
        f'        "Authorization: Bearer {api_key}"\n'
        '      ]\n'
        '    }\n'
        '  }\n'
        '}'
    )

    install_script = f"""#!/usr/bin/env bash
# EvolveRun · Claude Desktop one-shot installer (hosted MCP)
# Connects Claude Desktop to the hosted EvolveRun MCP server via mcp-remote.
# Requires Node.js (npx) — install from https://nodejs.org if it's missing.
set -euo pipefail

CFG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
URL="{url}"
API_KEY="{api_key}"

if ! command -v npx >/dev/null 2>&1; then
  echo "❌ npx (Node.js) not found. Install Node from https://nodejs.org and re-run."
  exit 1
fi

mkdir -p "$(dirname "$CFG")"
[[ -f "$CFG" ]] || echo '{{}}' > "$CFG"

# Patch the config in-place using Python — robust to existing servers.
/usr/bin/python3 - "$CFG" "$URL" "$API_KEY" <<'PY'
import json, sys
cfg_path, url, api_key = sys.argv[1:]
with open(cfg_path) as f:
    try: cfg = json.load(f)
    except Exception: cfg = {{}}
cfg.setdefault("mcpServers", {{}})
cfg["mcpServers"]["evolverun"] = {{
    "command": "npx",
    "args": ["-y", "mcp-remote", url, "--header", f"Authorization: Bearer {{api_key}}"],
}}
with open(cfg_path, "w") as f:
    json.dump(cfg, f, indent=2)
print("✅ Config patched")
PY

# Restart Claude Desktop so it picks up the new server.
if pgrep -x "Claude" > /dev/null; then
  echo "↻ Restarting Claude Desktop…"
  osascript -e 'quit app "Claude"' >/dev/null 2>&1 || true
  sleep 1
fi
open -a Claude
echo ""
echo "🎉 EvolveRun connected. Open Claude Desktop and try:"
echo "    \\"What was my last long run?\\""
"""

    return InstallSnippets(
        claude_desktop_config_snippet=config_snippet,
        macos_install_script=install_script,
        mcp_url=url,
        claude_config_file_path=claude_cfg,
    )


class KeySummary(BaseModel):
    id: str
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


def _generate_key() -> tuple[str, str]:
    """Return (full_key, hash). Full key is shown to the user once; hash is stored."""
    body = secrets.token_urlsafe(32)
    full = f"{KEY_PREFIX}{body}"
    digest = hashlib.sha256(full.encode()).hexdigest()
    return full, digest


@router.post("", response_model=CreateKeyReply, status_code=status.HTTP_201_CREATED)
def create_key(
    body: CreateKeyBody,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CreateKeyReply:
    """Generate a new API key. The plaintext key is returned **once**."""
    full_key, key_hash = _generate_key()
    prefix = full_key[: len(KEY_PREFIX) + 8]

    client = get_supabase_admin()
    result = (
        client.table("mcp_api_keys")
        .insert(
            {
                "user_id": user.id,
                "key_hash": key_hash,
                "key_prefix": prefix,
                "name": body.name,
            }
        )
        .execute()
    )
    row = result.data[0]
    return CreateKeyReply(
        id=row["id"],
        name=row["name"],
        key=full_key,
        key_prefix=prefix,
        created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
        install=_build_install_snippets(full_key),
    )


@router.get("", response_model=list[KeySummary])
def list_keys(user: Annotated[CurrentUser, Depends(get_current_user)]) -> list[KeySummary]:
    """List all keys (active + revoked) for the user."""
    client = get_supabase_admin()
    rows = (
        client.table("mcp_api_keys")
        .select("id, name, key_prefix, created_at, last_used_at, revoked_at")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .execute()
    )
    out: list[KeySummary] = []
    for r in rows.data or []:
        out.append(
            KeySummary(
                id=r["id"],
                name=r["name"],
                key_prefix=r["key_prefix"],
                created_at=datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")),
                last_used_at=(
                    datetime.fromisoformat(r["last_used_at"].replace("Z", "+00:00"))
                    if r.get("last_used_at")
                    else None
                ),
                revoked_at=(
                    datetime.fromisoformat(r["revoked_at"].replace("Z", "+00:00"))
                    if r.get("revoked_at")
                    else None
                ),
            )
        )
    return out


class ConnectorStatus(BaseModel):
    claude_connected: bool


@router.get("/status", response_model=ConnectorStatus)
def connector_status(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ConnectorStatus:
    """Whether this user has ever completed the Claude OAuth connect flow.

    OAuth tokens are stateless JWTs, so the only durable trace of a completed
    grant is the consumed-token ledger (migration 0008): redeeming an auth
    code or rotating a refresh token writes a row with the user's id. Any row
    therefore means "connected at least once". If the table doesn't exist yet
    (migration not applied) we report not-connected rather than failing the
    dashboard. NOTE: if a pruning job for oauth_consumed_tokens is ever
    added, this signal needs a real grants table instead.
    """
    client = get_supabase_admin()
    try:
        rows = (
            client.table("oauth_consumed_tokens")
            .select("jti")
            .eq("user_id", user.id)
            .limit(1)
            .execute()
        )
        return ConnectorStatus(claude_connected=bool(rows.data))
    except Exception:
        return ConnectorStatus(claude_connected=False)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_key(
    key_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> None:
    """Mark a key revoked. The MCP server rejects requests using revoked keys."""
    client = get_supabase_admin()
    result = (
        client.table("mcp_api_keys")
        .update({"revoked_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", key_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Key not found")

"""MCP API key management.

A user generates a key here, pastes it into Claude Desktop / ChatGPT, and the
MCP server uses it to identify them on every tool call. We store only a SHA-256
hash of the key so a database breach can't be turned into impersonation.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, get_current_user
from app.core.supabase import get_supabase_admin

router = APIRouter(prefix="/mcp-keys", tags=["mcp-keys"])

KEY_PREFIX = "evr_"  # so users can recognize them on sight


class CreateKeyBody(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class CreateKeyReply(BaseModel):
    id: str
    name: str
    key: str  # full key — returned ONCE
    key_prefix: str
    created_at: datetime


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

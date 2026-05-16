"""Helpers for the oauth_connections table.

All read/write of provider tokens flows through here so encryption is
applied consistently and there's a single audit point.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.crypto import decrypt, encrypt
from app.core.supabase import get_supabase_admin
from app.services.providers.base import ProviderTokens


def upsert_tokens(*, user_id: str, provider: str, tokens: ProviderTokens) -> None:
    """Insert or replace the user's stored tokens for a provider."""
    client = get_supabase_admin()
    payload: dict[str, Any] = {
        "user_id": user_id,
        "provider": provider,
        "provider_user_id": tokens.provider_user_id,
        "access_token_encrypted": encrypt(tokens.access_token),
        "refresh_token_encrypted": encrypt(tokens.refresh_token) if tokens.refresh_token else None,
        "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
        "scope": tokens.scope,
        "status": "active",
        "metadata": tokens.extra or {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    client.table("oauth_connections").upsert(
        payload, on_conflict="user_id,provider"
    ).execute()


def load_tokens(*, user_id: str, provider: str) -> ProviderTokens | None:
    """Read decrypted tokens, or None if user has no active connection."""
    client = get_supabase_admin()
    result = (
        client.table("oauth_connections")
        .select("*")
        .eq("user_id", user_id)
        .eq("provider", provider)
        .eq("status", "active")
        .maybe_single()
        .execute()
    )
    row = result.data if result else None
    if not row:
        return None

    expires_at = None
    if row.get("expires_at"):
        expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))

    return ProviderTokens(
        access_token=decrypt(row["access_token_encrypted"]),
        refresh_token=decrypt(row["refresh_token_encrypted"]) if row.get("refresh_token_encrypted") else None,
        expires_at=expires_at,
        scope=row.get("scope"),
        provider_user_id=row.get("provider_user_id"),
        extra=row.get("metadata") or {},
    )


def mark_status(*, user_id: str, provider: str, status: str) -> None:
    """Mark a connection as expired / revoked / error. Used by sync workers on failure."""
    client = get_supabase_admin()
    client.table("oauth_connections").update(
        {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("user_id", user_id).eq("provider", provider).execute()

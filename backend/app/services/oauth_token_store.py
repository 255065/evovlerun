"""Server-side state that makes our stateless OAuth JWTs single-use / revocable.

Two operations back the hardening in routers/oauth.py:

  consume_jti()    — atomically record a token's jti. Returns True the first
                     time (caller may proceed) and False if the jti was already
                     spent (replay of an auth code, or reuse of a rotated
                     refresh token).

  is_grant_revoked / revoke_grant — a per-(user, client) revocation marker so a
                     disconnect or a detected refresh-token reuse invalidates
                     every token issued for that grant at/before revoked_at.

Failure posture: a genuine duplicate-key error means "already spent" → reject.
Any *other* DB error (e.g. the migration hasn't been applied yet) is logged and
treated as "allow", so an infra hiccup degrades to today's behaviour instead of
locking every user out of the connector.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.supabase import get_supabase_admin

log = logging.getLogger(__name__)


def _is_duplicate(exc: Exception) -> bool:
    code = getattr(exc, "code", "") or ""
    return code == "23505" or "duplicate key" in str(exc).lower()


def consume_jti(jti: str, *, typ: str, user_id: str | None, client_id: str | None) -> bool:
    """Record a token jti as spent. Returns True if newly recorded, False if it
    was already present (replay/reuse)."""
    if not jti:
        # A token with no jti predates this hardening — allow but don't track.
        return True
    try:
        get_supabase_admin().table("oauth_consumed_tokens").insert(
            {"jti": jti, "typ": typ, "user_id": user_id, "client_id": client_id}
        ).execute()
        return True
    except Exception as exc:  # noqa: BLE001 — classify below
        if _is_duplicate(exc):
            return False
        log.warning("consume_jti soft-fail for %s (%s): %s", jti, typ, exc)
        return True


def revoke_grant(user_id: str, client_id: str) -> None:
    """Mark every token for (user_id, client_id) issued so far as invalid."""
    now = datetime.now(timezone.utc).isoformat()
    try:
        get_supabase_admin().table("oauth_revoked_grants").upsert(
            {"user_id": user_id, "client_id": client_id, "revoked_at": now},
            on_conflict="user_id,client_id",
        ).execute()
    except Exception:  # noqa: BLE001
        log.warning("revoke_grant failed for %s/%s", user_id, client_id, exc_info=True)


def is_grant_revoked(user_id: str, client_id: str, issued_at: int) -> bool:
    """True if the grant was revoked at/after the token's iat (so the token is
    invalid). Fails open (returns False) on any lookup error."""
    try:
        result = (
            get_supabase_admin()
            .table("oauth_revoked_grants")
            .select("revoked_at")
            .eq("user_id", user_id)
            .eq("client_id", client_id)
            .maybe_single()
            .execute()
        )
    except Exception:  # noqa: BLE001
        log.warning("is_grant_revoked lookup failed for %s/%s", user_id, client_id, exc_info=True)
        return False
    row = result.data if result else None
    if not row or not row.get("revoked_at"):
        return False
    revoked_at = datetime.fromisoformat(row["revoked_at"].replace("Z", "+00:00"))
    return revoked_at.timestamp() >= issued_at

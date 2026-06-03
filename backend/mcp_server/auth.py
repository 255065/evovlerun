"""API-key validation for the MCP server.

The user pastes the key into Claude Desktop's config; we hash it with SHA-256
and look it up in the mcp_api_keys table. Returns the user_id the key was
issued to, which all tools then use to scope their Supabase queries.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from app.core.supabase import get_supabase_admin

log = logging.getLogger(__name__)


class InvalidApiKeyError(Exception):
    """The provided key is unknown, revoked, or malformed."""


def resolve_user_id(api_key: str) -> str:
    """Validate an API key and return the associated user_id.

    Raises InvalidApiKeyError on any auth failure.
    Touches last_used_at on success (best-effort).
    """
    if not api_key:
        raise InvalidApiKeyError("Missing API key")

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    client = get_supabase_admin()
    result = (
        client.table("mcp_api_keys")
        .select("id, user_id, revoked_at")
        .eq("key_hash", key_hash)
        .maybe_single()
        .execute()
    )
    row = result.data if result else None
    if not row:
        raise InvalidApiKeyError("API key not recognized")
    if row.get("revoked_at"):
        raise InvalidApiKeyError("API key has been revoked")

    # Best-effort last-used timestamp.
    try:
        client.table("mcp_api_keys").update(
            {"last_used_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", row["id"]).execute()
    except Exception:
        log.warning("Failed to update last_used_at for key %s", row["id"], exc_info=True)

    return row["user_id"]


# Subscription states that grant access to the MCP product surface. Mirrors
# `has_subscription` in app/routers/billing.py so the API and the web paywall
# agree on what "subscribed" means.
ACTIVE_SUBSCRIPTION_STATES = {"active", "trialing"}


def user_has_active_subscription(user_id: str) -> bool:
    """Return True if the user's profile has an active/trialing subscription.

    Used to gate the MCP product surface (the connector IS the paid product).
    A missing profile, a Supabase error, or a null/other status all count as
    NOT subscribed — we fail closed so a lookup failure never hands out free
    access.
    """
    try:
        result = (
            get_supabase_admin()
            .table("profiles")
            .select("subscription_status")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
    except Exception:
        log.warning("Subscription lookup failed for user %s", user_id, exc_info=True)
        return False
    row = result.data if result else None
    status = (row or {}).get("subscription_status")
    return status in ACTIVE_SUBSCRIPTION_STATES

"""OAuth client registration storage.

Dynamic Client Registration (RFC 7591) is how Claude.ai introduces itself to
us: it POSTs its name + redirect URIs and we issue a client_id (+ optional
secret) that it uses for all subsequent OAuth requests.

We persist the registration in `oauth_clients` so the client_id survives
restarts. Secrets are hashed (SHA-256) before storage, like the API keys.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Any

from app.core.supabase import get_supabase_admin


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def register_client(
    *,
    client_name: str,
    redirect_uris: list[str],
    grant_types: list[str] | None = None,
    scopes: list[str] | None = None,
    is_public: bool = True,
) -> dict[str, Any]:
    """Issue a new OAuth client.

    Returns the client_id (and client_secret if non-public). The secret is
    shown ONCE — we store only its hash.
    """
    client_id = "evrc_" + secrets.token_urlsafe(18)
    client_secret = None if is_public else secrets.token_urlsafe(32)
    secret_hash = _hash(client_secret) if client_secret else None

    row = {
        "client_id": client_id,
        "client_secret_hash": secret_hash,
        "client_name": client_name,
        "redirect_uris": redirect_uris,
        "grant_types": grant_types or ["authorization_code"],
        "scopes": scopes or ["mcp"],
        "is_public": is_public,
    }
    get_supabase_admin().table("oauth_clients").insert(row).execute()

    out: dict[str, Any] = {
        "client_id": client_id,
        "client_name": client_name,
        "redirect_uris": redirect_uris,
        "grant_types": row["grant_types"],
        "scopes": row["scopes"],
        "token_endpoint_auth_method": "none" if is_public else "client_secret_post",
    }
    if client_secret:
        out["client_secret"] = client_secret
    return out


def load_client(client_id: str) -> dict[str, Any] | None:
    """Look up a client by client_id. Returns None if unknown."""
    result = (
        get_supabase_admin()
        .table("oauth_clients")
        .select("*")
        .eq("client_id", client_id)
        .maybe_single()
        .execute()
    )
    return result.data if result else None


def verify_client_secret(client_id: str, client_secret: str) -> bool:
    """Confidential clients must present their secret on /oauth/token."""
    row = load_client(client_id)
    if not row or not row.get("client_secret_hash"):
        return False
    return hmac.compare_digest(_hash(client_secret), row["client_secret_hash"])


def touch_client(client_id: str) -> None:
    """Bump last_used_at — best-effort, swallowed on failure."""
    try:
        get_supabase_admin().table("oauth_clients").update(
            {"last_used_at": datetime.now(timezone.utc).isoformat()}
        ).eq("client_id", client_id).execute()
    except Exception:
        pass


def redirect_uri_allowed(client: dict[str, Any], redirect_uri: str) -> bool:
    """Strict match — no wildcards. Claude.ai always sends an exact URI."""
    allowed = client.get("redirect_uris") or []
    return redirect_uri in allowed

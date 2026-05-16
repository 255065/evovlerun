"""Signed `state` tokens for OAuth flows.

OAuth callbacks arrive without our session cookie, so we encode the user_id
into the `state` parameter and verify its signature on the way back. This
removes the need for a separate state-tracking table.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import get_settings


def sign_state(*, user_id: str, provider: str, ttl_seconds: int = 600) -> str:
    """Mint a state token tying a user to a provider. Default TTL = 10 minutes."""
    settings = get_settings()
    if not settings.oauth_state_secret:
        raise RuntimeError("OAUTH_STATE_SECRET not configured")

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "prov": provider,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "nonce": secrets.token_urlsafe(8),
    }
    return jwt.encode(payload, settings.oauth_state_secret, algorithm="HS256")


def verify_state(state: str, *, expected_provider: str) -> str:
    """Validate state and return the user_id it was minted for. Raises on failure."""
    settings = get_settings()
    if not settings.oauth_state_secret:
        raise RuntimeError("OAUTH_STATE_SECRET not configured")

    try:
        payload = jwt.decode(state, settings.oauth_state_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError(f"Invalid OAuth state: {exc}") from exc

    if payload.get("prov") != expected_provider:
        raise ValueError("OAuth state provider mismatch")

    sub = payload.get("sub")
    if not sub:
        raise ValueError("OAuth state missing subject")
    return sub

"""JWT-based OAuth 2.1 helpers.

Authorization codes and access tokens are signed JWTs — no DB lookup needed
to verify them. Both are short-lived (codes: 60s, tokens: 1h by default) and
include enough claims to reconstruct who they're for and what they can do.

Why JWT instead of opaque tokens:
  • No race on token issuance and instant horizontal scale
  • Token verifier doesn't have to round-trip Supabase per MCP request
  • PKCE check is a single signature + claim check

The signing secret is OAUTH_STATE_SECRET (already used to sign the OAuth
`state` we send to wearable providers). Same key, different audience tag —
no token collision because the `typ` claim differs.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from typing import Any

from jose import jwt, JWTError

from app.config import get_settings

ISSUER = "evolverun-mcp"
ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Authorization code
# ---------------------------------------------------------------------------
def issue_authorization_code(
    *,
    user_id: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    code_challenge: str | None,
    code_challenge_method: str | None,
    ttl_seconds: int = 60,
) -> str:
    """Mint a one-time JWT authorization code.

    Claims:
      typ              "auth_code"   — distinguishes from access tokens
      sub              user_id       — the authenticated user
      aud              client_id     — only this client can redeem it
      redirect_uri     must match on exchange
      scope            granted scopes
      code_challenge   PKCE challenge (S256 hash of code_verifier)
      jti              random — caller checks with `has_been_redeemed` to
                       prevent replay (we don't persist it; rely on TTL)
    """
    settings = get_settings()
    now = int(time.time())
    payload = {
        "iss": ISSUER,
        "typ": "auth_code",
        "sub": user_id,
        "aud": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method or "S256",
        "iat": now,
        "exp": now + ttl_seconds,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.oauth_state_secret, algorithm=ALGORITHM)


def verify_authorization_code(
    code: str, *, expected_client_id: str, expected_redirect_uri: str
) -> dict[str, Any]:
    """Decode a code JWT and check audience + redirect_uri.

    Raises ValueError on any failure. Caller is responsible for PKCE check.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            code,
            settings.oauth_state_secret,
            algorithms=[ALGORITHM],
            audience=expected_client_id,
            issuer=ISSUER,
        )
    except JWTError as exc:
        raise ValueError(f"invalid authorization code: {exc}") from exc

    if payload.get("typ") != "auth_code":
        raise ValueError("wrong token type")
    if payload.get("redirect_uri") != expected_redirect_uri:
        raise ValueError("redirect_uri mismatch")
    return payload


# ---------------------------------------------------------------------------
# Access token
# ---------------------------------------------------------------------------
def issue_access_token(
    *,
    user_id: str,
    client_id: str,
    scope: str = "mcp",
    ttl_seconds: int = 3600,
) -> tuple[str, int]:
    """Mint an OAuth access token (JWT). Returns (token, expires_in_seconds)."""
    settings = get_settings()
    now = int(time.time())
    payload = {
        "iss": ISSUER,
        "typ": "access_token",
        "sub": user_id,
        "aud": client_id,
        "scope": scope,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return jwt.encode(payload, settings.oauth_state_secret, algorithm=ALGORITHM), ttl_seconds


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Verify an access token JWT. Returns claims or None if invalid.

    Skip audience check here — the resource server isn't trying to validate
    *which* client issued the token, only that we issued it and it hasn't
    expired. (Future hardening: pin to a known client list.)
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.oauth_state_secret,
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            options={"verify_aud": False},
        )
    except JWTError:
        return None
    if payload.get("typ") != "access_token":
        return None
    return payload


# ---------------------------------------------------------------------------
# PKCE
# ---------------------------------------------------------------------------
def verify_pkce(*, code_verifier: str, code_challenge: str, method: str) -> bool:
    """Validate a PKCE code_verifier against the stored challenge.

    Supports S256 (RFC 7636 §4.2) and plain. Claude.ai always uses S256.
    """
    if method == "plain":
        return code_verifier == code_challenge
    if method == "S256":
        digest = hashlib.sha256(code_verifier.encode()).digest()
        expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        return expected == code_challenge
    return False

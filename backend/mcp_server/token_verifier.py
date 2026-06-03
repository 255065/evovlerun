"""Bearer-token verifier for the HTTP MCP transport.

Accepts two token shapes:

  1. EvolveRun API keys (`evr_…`) — issued in /dashboard/mcp and pasted into
     Claude Desktop / Cursor / Claude Code. Validated by hash lookup in
     mcp_api_keys.
  2. OAuth access tokens (JWT) — issued by /oauth/token after a user
     completes the Claude.ai consent flow. Validated by signature alone.

Both flows resolve to a user_id which we attach to the request via FastMCP's
AuthContext (via the `client_id` field on AccessToken). When a tool runs it
reads that back via mcp_server/context.py:get_user_id().
"""

from __future__ import annotations

import logging

from mcp.server.auth.provider import AccessToken, TokenVerifier

from app.config import get_settings
from app.services.oauth_jwt import decode_access_token
from mcp_server.auth import (
    InvalidApiKeyError,
    resolve_user_id,
    user_has_active_subscription,
)

log = logging.getLogger(__name__)

API_KEY_PREFIX = "evr_"


class EvolveRunTokenVerifier(TokenVerifier):
    """Resolves either an EvolveRun API key or an OAuth JWT to a user_id."""

    async def verify_token(self, token: str) -> AccessToken | None:
        # Distinguish the two formats by prefix. Anything starting with
        # `evr_` is an API key; everything else we try as a JWT.
        if token.startswith(API_KEY_PREFIX):
            try:
                user_id = resolve_user_id(token)
            except InvalidApiKeyError as exc:
                log.debug("MCP auth rejected (api key): %s", exc)
                return None
            scopes = ["mcp"]
            expires_at = None
        else:
            payload = decode_access_token(token)
            if payload is None:
                log.debug("MCP auth rejected: token is neither valid API key nor JWT")
                return None
            user_id = payload["sub"]
            scopes = (payload.get("scope") or "mcp").split()
            expires_at = int(payload["exp"]) if payload.get("exp") else None

        # The MCP connector IS the paid product, so the subscription check has
        # to live here (the web paywall in middleware.ts only guards /dashboard,
        # not this API). Gated by ENFORCE_SUBSCRIPTION so dev/self-use can opt
        # out; MUST be true in production.
        if not self._subscription_ok(user_id):
            return None

        return AccessToken(token=token, client_id=user_id, scopes=scopes, expires_at=expires_at)

    @staticmethod
    def _subscription_ok(user_id: str) -> bool:
        if not get_settings().enforce_subscription:
            return True
        if user_has_active_subscription(user_id):
            return True
        log.info("MCP auth rejected: user %s has no active subscription", user_id)
        return False

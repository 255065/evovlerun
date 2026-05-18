"""Bearer-token verifier for the HTTP MCP transport.

MCP's HTTP transport (streamable-HTTP / SSE) authenticates each request with
an `Authorization: Bearer <token>` header. We treat the token as one of our
EvolveRun API keys (the `evr_…` strings users generate in /dashboard/mcp),
hash it, look it up in the mcp_api_keys table, and resolve it to a user_id
that gets attached to the request via FastMCP's AuthContext.

When a tool runs, it reads the user_id back out of the context — see
mcp_server/context.py:get_user_id().
"""

from __future__ import annotations

import logging

from mcp.server.auth.provider import AccessToken, TokenVerifier

from mcp_server.auth import InvalidApiKeyError, resolve_user_id

log = logging.getLogger(__name__)


class EvolveRunTokenVerifier(TokenVerifier):
    """Resolves an EvolveRun API key to a user-scoped AccessToken.

    We stuff the user_id into `client_id` because that's the field FastMCP's
    middleware exposes downstream and it's the only piece of identity our
    tools need.
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            user_id = resolve_user_id(token)
        except InvalidApiKeyError as exc:
            log.debug("MCP auth rejected: %s", exc)
            return None
        return AccessToken(
            token=token,
            client_id=user_id,
            scopes=["mcp"],
            expires_at=None,
        )

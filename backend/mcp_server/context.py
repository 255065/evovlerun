"""Per-request user binding for the MCP server.

We support two transport modes:

  stdio (Claude Desktop)
    One Python process per user. The API key arrives in EVOLVERUN_API_KEY at
    startup, we resolve it once, and every tool call reads the same user_id.

  streamable-http (hosted, multi-user)
    One process serves every user. The API key arrives in each request's
    Authorization header. FastMCP's TokenVerifier resolves it, the
    AuthContextMiddleware stuffs the authenticated user into an MCP-managed
    contextvar, and we read it back here when a tool needs to know the user.

`get_user_id()` is the single read-path tools call — they don't care which
transport they're running under.
"""

from __future__ import annotations

import contextvars
import os

from mcp.server.auth.middleware.auth_context import auth_context_var

from mcp_server.auth import InvalidApiKeyError, resolve_user_id

# stdio cache: set once by bind_user_from_env() and read for the lifetime of
# the process. ContextVar (rather than a module global) so a future test that
# runs multiple sessions in one process stays isolated.
_stdio_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "evolverun_stdio_user_id", default=None
)


def bind_user_from_env() -> str:
    """stdio path: resolve EVOLVERUN_API_KEY once at startup."""
    key = os.environ.get("EVOLVERUN_API_KEY", "").strip()
    if not key:
        raise InvalidApiKeyError(
            "EVOLVERUN_API_KEY not set. Generate one at "
            "http://localhost:3000/dashboard/mcp and add it to your Claude config."
        )
    user_id = resolve_user_id(key)
    _stdio_user_id.set(user_id)
    return user_id


def get_user_id() -> str:
    """Return the user_id for the current call.

    Resolution order:
      1. HTTP auth context (set by AuthContextMiddleware per request)
      2. stdio binding (set by bind_user_from_env at process start)

    Raises if neither is set — which means the server was misconfigured.
    """
    # HTTP path
    auth_user = auth_context_var.get()
    if auth_user is not None:
        # FastMCP stores AccessToken.client_id on the user's access_token attr.
        token = getattr(auth_user, "access_token", None)
        if token and getattr(token, "client_id", None):
            return token.client_id

    # stdio path
    uid = _stdio_user_id.get()
    if uid:
        return uid

    raise RuntimeError(
        "MCP server context not bound — neither HTTP auth nor stdio binding present"
    )

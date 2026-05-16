"""Per-process user binding for the MCP server.

In stdio transport (Claude Desktop), one process serves exactly one user, so
we resolve the user_id once at startup from the EVOLVERUN_API_KEY env var.
Tools call `get_user_id()` to scope their queries.

For multi-user HTTP transport in the future, this will need to switch to
per-request resolution.
"""

from __future__ import annotations

import os

from mcp_server.auth import InvalidApiKeyError, resolve_user_id

_user_id: str | None = None


def bind_user_from_env() -> str:
    """Resolve the API key from EVOLVERUN_API_KEY and cache the user_id."""
    global _user_id
    key = os.environ.get("EVOLVERUN_API_KEY", "").strip()
    if not key:
        raise InvalidApiKeyError(
            "EVOLVERUN_API_KEY not set. Generate one at "
            "http://localhost:3000/dashboard/mcp and add it to your Claude config."
        )
    _user_id = resolve_user_id(key)
    return _user_id


def get_user_id() -> str:
    """Return the user_id bound at startup. Raises if bind has not been called."""
    if _user_id is None:
        raise RuntimeError("MCP server context not bound — call bind_user_from_env() first")
    return _user_id

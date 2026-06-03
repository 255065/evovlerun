"""Per-IP rate limiting for public, unauthenticated endpoints.

Implemented as a FastAPI dependency (not a decorator) so it never alters the
endpoint signature — decorators that wrap the handler break FastAPI's body
parsing. In-memory moving-window via the `limits` library; fine for a single
Railway instance as a coarse abuse backstop.

Usage:
    @router.post("/register", dependencies=[Depends(rate_limit("10/minute"))])
"""

from __future__ import annotations

from fastapi import HTTPException, Request, status
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

_storage = MemoryStorage()
_limiter = MovingWindowRateLimiter(_storage)


def rate_limit(limit: str):
    """Build a dependency enforcing `limit` (e.g. "10/minute") per client IP."""
    item = parse(limit)

    def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "anonymous"
        # Scope the bucket per path so endpoints don't share a budget.
        if not _limiter.hit(item, client_ip, request.url.path):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate limit exceeded",
            )

    return dependency

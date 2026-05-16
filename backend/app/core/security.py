"""Auth dependency: verifies Supabase JWTs and exposes the current user.

Supports both the new asymmetric ECC/RSA system (JWKS) and the legacy HS256
shared-secret system. Picks the right one based on the token's `alg` header.
"""

import time
from functools import lru_cache
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=True)

# Algorithms we accept. ES256 = ECC P-256 (new Supabase default). RS256 in case
# Supabase rotates to RSA. HS256 = legacy shared-secret.
ASYMMETRIC_ALGOS = {"ES256", "RS256", "EdDSA"}
SYMMETRIC_ALGOS = {"HS256"}


class CurrentUser(BaseModel):
    id: str
    email: str | None = None
    role: str | None = None


class _JWKSCache:
    """In-process cache for the JWKS document. Refreshes every TTL seconds."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._ttl = ttl_seconds
        self._jwks: dict[str, Any] | None = None
        self._fetched_at: float = 0.0

    def get(self, jwks_url: str) -> dict[str, Any]:
        now = time.time()
        if self._jwks is None or (now - self._fetched_at) > self._ttl:
            response = httpx.get(jwks_url, timeout=10.0)
            response.raise_for_status()
            self._jwks = response.json()
            self._fetched_at = now
        return self._jwks

    def invalidate(self) -> None:
        self._jwks = None
        self._fetched_at = 0.0


@lru_cache
def _jwks_cache() -> _JWKSCache:
    return _JWKSCache()


def _jwks_url(settings: Settings) -> str:
    base = settings.supabase_url.rstrip("/")
    if not base:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL not configured",
        )
    return f"{base}/auth/v1/.well-known/jwks.json"


def _find_key(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


def _verify_asymmetric(token: str, alg: str, kid: str, settings: Settings) -> dict[str, Any]:
    cache = _jwks_cache()
    jwks = cache.get(_jwks_url(settings))
    key = _find_key(jwks, kid)
    if key is None:
        # Maybe the project just rotated keys — refresh once and retry.
        cache.invalidate()
        jwks = cache.get(_jwks_url(settings))
        key = _find_key(jwks, kid)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"No JWKS key matching kid={kid}",
        )
    return jwt.decode(token, key, algorithms=[alg], audience="authenticated")


def _verify_symmetric(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signed with HS256 but SUPABASE_JWT_SECRET is not configured",
        )
    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        audience="authenticated",
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    """Decode and verify a Supabase access token. Returns the authenticated user."""
    token = credentials.credentials
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Malformed token: {exc}",
        ) from exc

    alg = header.get("alg")
    kid = header.get("kid")

    try:
        if alg in ASYMMETRIC_ALGOS and kid:
            payload = _verify_asymmetric(token, alg, kid, settings)
        elif alg in SYMMETRIC_ALGOS:
            payload = _verify_symmetric(token, settings)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unsupported JWT algorithm: {alg}",
            )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    return CurrentUser(
        id=sub,
        email=payload.get("email"),
        role=payload.get("role"),
    )

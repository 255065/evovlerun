"""OAuth 2.1 server endpoints — what Claude.ai's custom-connector flow hits.

The shape we implement:

  POST /oauth/register      RFC 7591 Dynamic Client Registration
  GET  /oauth/authorize     Redirects to the frontend consent page
  POST /oauth/approve       Frontend posts here when user clicks "Allow";
                            we mint an authorization code and 302 back to
                            the client's redirect_uri.
  POST /oauth/token         Exchange code (+ PKCE verifier) for access token,
                            or exchange a refresh token for a fresh pair.

The token response includes a long-lived refresh token, and /oauth/token
accepts `grant_type=refresh_token` so Claude.ai can silently renew its 1h
access token instead of forcing the user to reconnect. Refresh tokens are
rotated on every use.
"""

from __future__ import annotations

import logging
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.services.oauth_clients import (
    load_client,
    redirect_uri_allowed,
    register_client,
    touch_client,
    verify_client_secret,
)
from app.services.oauth_jwt import (
    issue_access_token,
    issue_authorization_code,
    issue_refresh_token,
    verify_authorization_code,
    verify_pkce,
    verify_refresh_token,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/oauth", tags=["oauth"])


# ---------------------------------------------------------------------------
# Dynamic Client Registration  (RFC 7591)
# ---------------------------------------------------------------------------
class RegisterBody(BaseModel):
    client_name: str | None = Field(default=None)
    redirect_uris: list[str] = Field(min_length=1, max_length=10)
    grant_types: list[str] | None = None
    token_endpoint_auth_method: str | None = None  # "none" → public PKCE client
    scope: str | None = None


@router.post("/register")
def register(body: RegisterBody) -> dict:
    """Claude.ai POSTs here on first connector setup. No auth required —
    that's the point of DCR. We accept any caller, but only mint a client_id;
    no actual access is granted until a user completes the consent flow."""
    is_public = (body.token_endpoint_auth_method or "none") == "none"
    scopes = (body.scope or "mcp").split() if body.scope else ["mcp"]
    grant_types = body.grant_types or ["authorization_code"]
    name = body.client_name or "Unnamed MCP client"

    issued = register_client(
        client_name=name,
        redirect_uris=body.redirect_uris,
        grant_types=grant_types,
        scopes=scopes,
        is_public=is_public,
    )
    return issued


# ---------------------------------------------------------------------------
# Authorize  — redirect to frontend consent page
# ---------------------------------------------------------------------------
@router.get("/authorize")
def authorize(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """Initial step of the auth-code flow.

    Claude.ai sends the user's browser here with:
      response_type=code
      client_id=...
      redirect_uri=...
      scope=mcp
      state=...
      code_challenge=...
      code_challenge_method=S256

    We validate the client + redirect_uri, then redirect the browser to our
    own frontend /oauth/consent page where the user sees what's being granted
    and clicks Allow.
    """
    q = request.query_params

    client_id = q.get("client_id")
    redirect_uri = q.get("redirect_uri")
    response_type = q.get("response_type", "code")
    state = q.get("state", "")
    scope = q.get("scope", "mcp")
    code_challenge = q.get("code_challenge")
    code_challenge_method = q.get("code_challenge_method", "S256")

    if response_type != "code":
        raise HTTPException(status_code=400, detail="unsupported response_type")
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=400, detail="missing client_id or redirect_uri")
    # PKCE is mandatory (OAuth 2.1). Reject the request up front if the client
    # didn't send an S256 challenge, so a code can never be minted without one
    # — otherwise the exchange-time check can be downgrade-bypassed.
    if not code_challenge or code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="PKCE required: code_challenge with S256")

    client = load_client(client_id)
    if not client:
        raise HTTPException(status_code=400, detail="unknown client_id")
    if not redirect_uri_allowed(client, redirect_uri):
        raise HTTPException(status_code=400, detail="redirect_uri not registered for this client")

    # Hand off to the frontend consent screen. The frontend will require login,
    # show the consent UI, and POST back to /oauth/approve.
    consent_params = {
        "client_id": client_id,
        "client_name": client.get("client_name") or "",
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": scope,
        "code_challenge": code_challenge or "",
        "code_challenge_method": code_challenge_method,
    }
    target = f"{settings.frontend_url.rstrip('/')}/oauth/consent?" + urlencode(consent_params)
    return RedirectResponse(target, status_code=302)


# ---------------------------------------------------------------------------
# Approve — frontend posts here when the user clicks Allow
# ---------------------------------------------------------------------------
class ApproveBody(BaseModel):
    client_id: str
    redirect_uri: str
    state: str = ""
    scope: str = "mcp"
    code_challenge: str | None = None
    code_challenge_method: str | None = "S256"


@router.post("/approve")
def approve(
    body: ApproveBody,
    user: Annotated[CurrentUser, Depends(get_current_user)],
):
    """Issue an authorization code and tell the frontend where to redirect."""
    if not body.code_challenge or (body.code_challenge_method or "S256") != "S256":
        raise HTTPException(status_code=400, detail="PKCE required: code_challenge with S256")

    client = load_client(body.client_id)
    if not client:
        raise HTTPException(status_code=400, detail="unknown client_id")
    if not redirect_uri_allowed(client, body.redirect_uri):
        raise HTTPException(status_code=400, detail="redirect_uri not registered")

    code = issue_authorization_code(
        user_id=user.id,
        client_id=body.client_id,
        redirect_uri=body.redirect_uri,
        scope=body.scope,
        code_challenge=body.code_challenge,
        code_challenge_method=body.code_challenge_method,
    )

    # Build the final redirect Claude.ai will land on.
    params = {"code": code}
    if body.state:
        params["state"] = body.state
    redirect_url = body.redirect_uri + ("&" if "?" in body.redirect_uri else "?") + urlencode(params)
    return {"redirect_url": redirect_url}


# ---------------------------------------------------------------------------
# Token  — exchange code for access token
# ---------------------------------------------------------------------------
@router.post("/token")
def token(
    grant_type: Annotated[str, Form()],
    code: Annotated[str | None, Form()] = None,
    redirect_uri: Annotated[str | None, Form()] = None,
    client_id: Annotated[str | None, Form()] = None,
    client_secret: Annotated[str | None, Form()] = None,
    code_verifier: Annotated[str | None, Form()] = None,
    refresh_token: Annotated[str | None, Form()] = None,
):
    """Standard OAuth token endpoint — RFC 6749 + RFC 7636 (PKCE).

    Supports two grants:
      authorization_code  — exchange a code (+ PKCE verifier) for tokens
      refresh_token       — exchange a refresh token for a fresh token pair
    """
    if grant_type == "authorization_code":
        return _grant_authorization_code(
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            client_secret=client_secret,
            code_verifier=code_verifier,
        )
    if grant_type == "refresh_token":
        return _grant_refresh_token(
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
        )
    raise HTTPException(status_code=400, detail={"error": "unsupported_grant_type"})


def _require_client(client_id: str | None, client_secret: str | None) -> None:
    """Validate the client exists and, if confidential, presents its secret."""
    if not client_id:
        raise HTTPException(status_code=400, detail={"error": "invalid_request"})
    client = load_client(client_id)
    if not client:
        raise HTTPException(status_code=400, detail={"error": "invalid_client"})
    if not client.get("is_public", True):
        if not client_secret or not verify_client_secret(client_id, client_secret):
            raise HTTPException(status_code=401, detail={"error": "invalid_client"})


def _token_response(*, user_id: str, client_id: str, scope: str) -> dict:
    """Mint a fresh access + (rotated) refresh token pair."""
    access, expires_in = issue_access_token(user_id=user_id, client_id=client_id, scope=scope)
    refresh = issue_refresh_token(user_id=user_id, client_id=client_id, scope=scope)
    touch_client(client_id)
    return {
        "access_token": access,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "refresh_token": refresh,
        "scope": scope,
    }


def _grant_authorization_code(
    *,
    code: str | None,
    redirect_uri: str | None,
    client_id: str | None,
    client_secret: str | None,
    code_verifier: str | None,
) -> dict:
    if not code or not redirect_uri or not client_id:
        raise HTTPException(status_code=400, detail={"error": "invalid_request"})

    _require_client(client_id, client_secret)

    try:
        payload = verify_authorization_code(
            code, expected_client_id=client_id, expected_redirect_uri=redirect_uri
        )
    except ValueError as exc:
        log.warning("auth code rejected: %s", exc)
        raise HTTPException(status_code=400, detail={"error": "invalid_grant", "detail": str(exc)})

    # PKCE check. Every code is minted with an S256 challenge (enforced at
    # /authorize and /approve), so a code missing one — or carrying a non-S256
    # method — is a downgrade attempt and is rejected outright.
    challenge = payload.get("code_challenge")
    method = payload.get("code_challenge_method") or "S256"
    if not challenge or method != "S256":
        raise HTTPException(status_code=400, detail={"error": "invalid_grant", "detail": "PKCE required"})
    if not code_verifier:
        raise HTTPException(status_code=400, detail={"error": "invalid_grant", "detail": "code_verifier required"})
    if not verify_pkce(code_verifier=code_verifier, code_challenge=challenge, method=method):
        raise HTTPException(status_code=400, detail={"error": "invalid_grant", "detail": "PKCE check failed"})

    return _token_response(
        user_id=payload["sub"], client_id=client_id, scope=payload.get("scope", "mcp")
    )


def _grant_refresh_token(
    *,
    refresh_token: str | None,
    client_id: str | None,
    client_secret: str | None,
) -> dict:
    if not refresh_token or not client_id:
        raise HTTPException(status_code=400, detail={"error": "invalid_request"})

    _require_client(client_id, client_secret)

    try:
        payload = verify_refresh_token(refresh_token, expected_client_id=client_id)
    except ValueError as exc:
        log.warning("refresh token rejected: %s", exc)
        raise HTTPException(status_code=400, detail={"error": "invalid_grant", "detail": str(exc)})

    return _token_response(
        user_id=payload["sub"], client_id=client_id, scope=payload.get("scope", "mcp")
    )

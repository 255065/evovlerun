"""Provider OAuth + sync routes.

The frontend opens the authorize URL we return from /authorize. The provider
redirects back to /callback, we exchange the code, store encrypted tokens,
and trigger an initial sync. The frontend is then redirected to the
connections page with a status param.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# Side-effect imports — provider modules call register_provider() at import time.
from app.services.providers import strava as _strava  # noqa: F401  pylint: disable=unused-import
from app.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.services.connections import load_tokens, mark_status, upsert_tokens
from app.services.oauth_state import verify_state
from app.services.providers import get_provider, list_providers
from app.services.providers.base import ProviderAuthError, ProviderError
from app.services.workouts import upsert_activities

log = logging.getLogger(__name__)
router = APIRouter(prefix="/providers", tags=["providers"])

# How far back to pull on first connect.
INITIAL_SYNC_DAYS = 90


class AuthorizeResponse(BaseModel):
    authorize_url: str


class ConnectionStatus(BaseModel):
    provider: str
    connected: bool
    provider_user_id: str | None = None
    expires_at: datetime | None = None
    scope: str | None = None


def _redirect_uri(settings: Settings, provider_slug: str) -> str:
    return f"{settings.backend_public_url.rstrip('/')}/providers/{provider_slug}/callback"


def _frontend_redirect(settings: Settings, status_msg: str, provider_slug: str) -> str:
    return (
        f"{settings.frontend_url.rstrip('/')}/dashboard/connections"
        f"?provider={provider_slug}&status={status_msg}"
    )


# -- list available providers --------------------------------------------------
@router.get("", response_model=list[str])
def available_providers() -> list[str]:
    """Slugs of providers that are configured and ready to connect."""
    return list_providers()


# -- start OAuth ---------------------------------------------------------------
@router.post("/{provider_slug}/authorize", response_model=AuthorizeResponse)
def authorize(
    provider_slug: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthorizeResponse:
    """Build the provider authorize URL the frontend should redirect the user to."""
    try:
        provider = get_provider(provider_slug)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    redirect_uri = _redirect_uri(settings, provider_slug)
    flow = provider.start_oauth(user_id=user.id, redirect_uri=redirect_uri)
    return AuthorizeResponse(authorize_url=flow.authorize_url)


# -- OAuth callback ------------------------------------------------------------
@router.get("/{provider_slug}/callback")
async def callback(
    provider_slug: str,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """Provider redirects user here with ?code=...&state=... after they approve."""
    error = request.query_params.get("error")
    if error:
        log.warning("Provider %s returned OAuth error: %s", provider_slug, error)
        return RedirectResponse(_frontend_redirect(settings, f"denied:{error}", provider_slug))

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code or not state:
        return RedirectResponse(_frontend_redirect(settings, "missing_params", provider_slug))

    try:
        provider = get_provider(provider_slug)
    except KeyError:
        return RedirectResponse(_frontend_redirect(settings, "unknown_provider", provider_slug))

    try:
        user_id = verify_state(state, expected_provider=provider_slug)
    except ValueError as exc:
        log.warning("OAuth state rejected for %s: %s", provider_slug, exc)
        return RedirectResponse(_frontend_redirect(settings, "bad_state", provider_slug))

    redirect_uri = _redirect_uri(settings, provider_slug)
    try:
        tokens = await provider.complete_oauth(code=code, state=state, redirect_uri=redirect_uri)
    except ProviderError as exc:
        log.exception("complete_oauth failed for %s", provider_slug)
        return RedirectResponse(_frontend_redirect(settings, f"exchange_failed:{exc}", provider_slug))

    upsert_tokens(user_id=user_id, provider=provider_slug, tokens=tokens)

    # Best-effort initial sync. Failure here doesn't break the connection —
    # the user can retry via /sync.
    try:
        since = datetime.now(timezone.utc) - timedelta(days=INITIAL_SYNC_DAYS)
        activities = await provider.fetch_activities(tokens, since=since)
        written = upsert_activities(user_id=user_id, activities=activities)
        log.info("Initial sync for %s/%s: wrote %d activities", user_id, provider_slug, written)
    except ProviderError as exc:
        log.warning("Initial sync failed for %s/%s: %s", user_id, provider_slug, exc)
        return RedirectResponse(_frontend_redirect(settings, "connected_no_sync", provider_slug))

    return RedirectResponse(_frontend_redirect(settings, "connected", provider_slug))


# -- status --------------------------------------------------------------------
@router.get("/{provider_slug}/status", response_model=ConnectionStatus)
def connection_status(
    provider_slug: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ConnectionStatus:
    """Tell the frontend whether this user has a working connection for a provider."""
    tokens = load_tokens(user_id=user.id, provider=provider_slug)
    if not tokens:
        return ConnectionStatus(provider=provider_slug, connected=False)
    return ConnectionStatus(
        provider=provider_slug,
        connected=True,
        provider_user_id=tokens.provider_user_id,
        expires_at=tokens.expires_at,
        scope=tokens.scope,
    )


# -- manual sync ---------------------------------------------------------------
@router.post("/{provider_slug}/sync")
async def manual_sync(
    provider_slug: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    days: int = 30,
) -> dict[str, int | str]:
    """User-triggered re-sync for the last N days."""
    try:
        provider = get_provider(provider_slug)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    tokens = load_tokens(user_id=user.id, provider=provider_slug)
    if not tokens:
        raise HTTPException(status_code=400, detail=f"Not connected to {provider_slug}")

    try:
        tokens = await provider.refresh(tokens)
        if tokens.access_token != (load_tokens(user_id=user.id, provider=provider_slug) or tokens).access_token:
            upsert_tokens(user_id=user.id, provider=provider_slug, tokens=tokens)

        since = datetime.now(timezone.utc) - timedelta(days=days)
        activities = await provider.fetch_activities(tokens, since=since)
        written = upsert_activities(user_id=user.id, activities=activities)
        return {"provider": provider_slug, "synced": written}
    except ProviderAuthError as exc:
        mark_status(user_id=user.id, provider=provider_slug, status="expired")
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# -- disconnect ----------------------------------------------------------------
@router.delete("/{provider_slug}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect(
    provider_slug: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> None:
    """Mark the connection revoked. Token row stays for audit; we just stop using it."""
    mark_status(user_id=user.id, provider=provider_slug, status="revoked")


# -- Strava webhook ------------------------------------------------------------
# Strava webhooks need TWO endpoints with the same path:
#   GET  → subscription verification (hub challenge echo)
#   POST → event delivery
@router.get("/strava/webhook")
def strava_webhook_verify(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    """Strava sends a one-time GET to verify the endpoint when you create a subscription."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode != "subscribe" or token != settings.strava_webhook_verify_token or not challenge:
        raise HTTPException(status_code=403, detail="Webhook verification failed")
    return {"hub.challenge": challenge}


@router.post("/strava/webhook", status_code=200)
async def strava_webhook_event(request: Request) -> dict[str, str]:
    """Strava push for create/update/delete events.

    We acknowledge fast (must respond within 2s). Real sync happens in the
    background — TODO when we wire a job queue.
    """
    payload = await request.json()
    log.info("Strava webhook event: %s", payload)
    # TODO: enqueue background job to fetch this single activity by id
    return {"status": "received"}

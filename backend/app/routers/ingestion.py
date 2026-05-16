"""Data-ingestion endpoints — wearable webhooks and manual sync triggers."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.security import CurrentUser, get_current_user

router = APIRouter(prefix="/ingest", tags=["ingestion"])

Provider = Literal["garmin", "strava", "oura", "whoop", "apple_health"]


class SyncRequest(BaseModel):
    provider: Provider


class SyncResponse(BaseModel):
    status: str
    provider: Provider
    queued: bool


@router.post("/sync", response_model=SyncResponse)
def trigger_sync(
    body: SyncRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> SyncResponse:
    """Manually trigger a sync for one of the user's connected providers.

    Real implementation will enqueue a background job that pulls fresh
    activities, sleep, HRV etc. from the provider API.
    """
    # TODO: enqueue background sync job for (user.id, body.provider)
    return SyncResponse(status="queued", provider=body.provider, queued=True)


@router.post("/webhook/{provider}")
async def receive_webhook(provider: Provider, request: Request) -> dict[str, str]:
    """Receive push notifications from wearable providers.

    Each provider has its own signature scheme — verify per provider in real impl.
    """
    # TODO: verify provider signature, parse payload, enqueue ingestion job
    _ = await request.body()
    return {"status": "received", "provider": provider}

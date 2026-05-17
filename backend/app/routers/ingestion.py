"""Data-ingestion endpoints — wearable webhooks and manual sync triggers."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, get_current_user
from app.services.garmin_sync import sync_full, sync_incremental

router = APIRouter(prefix="/ingest", tags=["ingestion"])

Provider = Literal["garmin", "strava", "oura", "whoop", "apple_health"]


class SyncRequest(BaseModel):
    provider: Provider
    mode: Literal["full", "incremental"] = "incremental"
    days_back: int = Field(default=90, ge=1, le=365, description="History window when mode=full")


class SyncResponse(BaseModel):
    status: str
    provider: Provider
    report: dict


@router.post("/sync", response_model=SyncResponse)
async def trigger_sync(
    body: SyncRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> SyncResponse:
    """Manually trigger a sync for one of the user's connected providers.

    `mode=full` backfills history (default 90 days). `mode=incremental` does a
    light refresh of the last few days. Garmin is the only provider wired up
    here for now — Strava goes through webhooks, others are still stubs.
    """
    if body.provider == "garmin":
        if body.mode == "full":
            report = await sync_full(user_id=user.id, days_back=body.days_back)
        else:
            report = await sync_incremental(user_id=user.id)
        return SyncResponse(status=report.get("status", "ok"), provider=body.provider, report=dict(report))

    # Other providers will land here as we wire them up.
    raise HTTPException(
        status_code=501,
        detail=f"Sync for provider '{body.provider}' is not implemented yet.",
    )


@router.post("/webhook/{provider}")
async def receive_webhook(provider: Provider, request: Request) -> dict[str, str]:
    """Receive push notifications from wearable providers.

    Each provider has its own signature scheme — verify per provider in real impl.
    """
    # TODO: verify provider signature, parse payload, enqueue ingestion job
    _ = await request.body()
    return {"status": "received", "provider": provider}

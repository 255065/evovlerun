"""Performance model endpoints — recompute + timeline reads."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, get_current_user
from app.core.supabase import get_supabase_admin
from app.services.performance import recompute_for_user

router = APIRouter(prefix="/performance", tags=["performance"])


class RecomputeBody(BaseModel):
    lookback_days: int = Field(default=180, ge=14, le=730)


@router.post("/recompute")
def recompute(
    body: RecomputeBody,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    """Recompute TRIMP/TSS per workout + daily CTL/ATL/TSB/ACWR.

    Cheap and idempotent — call it after a sync, or on a daily cron.
    """
    return recompute_for_user(user_id=user.id, lookback_days=body.lookback_days)


class TimelinePoint(BaseModel):
    snapshot_date: date
    ctl: float | None = None
    atl: float | None = None
    tsb: float | None = None
    acwr: float | None = None


@router.get("/timeline")
def timeline(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    days: int = 90,
) -> dict:
    """Return the per-day fitness/fatigue/form series for charting."""
    since = (date.today() - timedelta(days=days)).isoformat()
    client = get_supabase_admin()
    rows = (
        client.table("performance_profiles")
        .select("snapshot_date, fitness_ctl, fatigue_atl, form_tsb, acwr")
        .eq("user_id", user.id)
        .gte("snapshot_date", since)
        .order("snapshot_date")
        .execute()
        .data
        or []
    )
    return {
        "days": days,
        "points": [
            {
                "snapshot_date": r["snapshot_date"],
                "ctl": r.get("fitness_ctl"),
                "atl": r.get("fatigue_atl"),
                "tsb": r.get("form_tsb"),
                "acwr": r.get("acwr"),
            }
            for r in rows
        ],
    }

"""Limiter detection endpoints."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import CurrentUser, get_current_user
from app.core.supabase import get_supabase_admin
from app.services.limiter_engine import detect_limiter, gather_evidence

log = logging.getLogger(__name__)
router = APIRouter(prefix="/limiter", tags=["limiter"])


@router.post("/analyze")
def analyze(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict:
    """Run a fresh Opus-based limiter analysis. Cost ≈ 1 Opus call."""
    try:
        return detect_limiter(user_id=user.id)
    except RuntimeError as exc:
        # Missing API key — surface cleanly to the frontend.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("limiter analyze failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/evidence")
def evidence(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict:
    """Return the same evidence bundle that gets sent to Opus, without calling it.

    Useful for debugging the input snapshot or letting the frontend show a
    "data Claude will see" preview.
    """
    return gather_evidence(user.id)


class LimiterRecord(BaseModel):
    id: str
    detected_at: str
    primary_limiter: str
    secondary_limiter: str | None = None
    confidence: float
    recommended_focus: str | None = None


@router.get("/latest")
def latest(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict:
    """Most recent limiter determination + reasoning."""
    client = get_supabase_admin()
    rows = (
        client.table("limiter_history")
        .select("*")
        .eq("user_id", user.id)
        .order("detected_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return {"available": False}
    r = rows[0]
    ev = r.get("evidence") or {}
    return {
        "available": True,
        "detected_at": r["detected_at"],
        "primary_limiter": r["primary_limiter"],
        "secondary_limiter": r.get("secondary_limiter"),
        "confidence": float(r["confidence"]),
        "recommended_focus": r.get("recommended_focus"),
        "key_observations": ev.get("key_observations") or [],
        "supporting_data_points": ev.get("supporting_data_points") or [],
        "physiology_explanation": ev.get("physiology_explanation"),
        "alternative_considered": ev.get("alternative_considered"),
    }


@router.get("/history")
def history(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    days: int = 180,
) -> dict:
    """All limiter calls in a window — used to chart how the limiter shifts."""
    since = (date.today() - timedelta(days=days)).isoformat()
    client = get_supabase_admin()
    rows = (
        client.table("limiter_history")
        .select("id, detected_at, primary_limiter, secondary_limiter, confidence, recommended_focus")
        .eq("user_id", user.id)
        .gte("detected_at", since)
        .order("detected_at", desc=True)
        .execute()
        .data
        or []
    )
    return {"days": days, "count": len(rows), "history": rows}

"""Metrics + trends + post-workout AI endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import CurrentUser, get_current_user
from app.services.metrics_engine import compute_all_metrics
from app.services.post_workout_engine import analyze_recent_workouts, analyze_workout
from app.services.trend_engine import compute_trends

log = logging.getLogger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("/recompute")
def recompute(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict:
    """Recompute VDOT, VO2max, threshold, running economy, fatigue/recovery scores."""
    return compute_all_metrics(user_id=user.id)


@router.get("/trends")
def trends(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict:
    """4 / 8 / 12-week trend cards for every key metric."""
    return compute_trends(user.id)


@router.post("/post-workout/scan")
def scan_recent(user: Annotated[CurrentUser, Depends(get_current_user)], hours: int = 48) -> dict:
    """Find key sessions in the window that haven't been analyzed and analyze them."""
    try:
        return analyze_recent_workouts(user_id=user.id, since_hours=hours)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/post-workout/{workout_id}")
def analyze_one(
    workout_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    """Force a fresh analysis of one specific workout. Idempotent."""
    try:
        return analyze_workout(user_id=user.id, workout_id=workout_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

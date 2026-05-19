"""Metrics + trends endpoints.

V1 has no onboard AI — the post-workout LLM analyzer that used to live
here was removed. Recompute (Banister TRIMP / Coggan hrTSS) and trends
are pure math, so they stay.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user
from app.services.metrics_engine import compute_all_metrics
from app.services.trend_engine import compute_trends

log = logging.getLogger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("/recompute")
def recompute(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict:
    """Recompute CTL / ATL / TSB / ACWR and VDOT-style fitness markers."""
    return compute_all_metrics(user_id=user.id)


@router.get("/trends")
def trends(user: Annotated[CurrentUser, Depends(get_current_user)]) -> dict:
    """4 / 8 / 12-week trend cards for every key metric."""
    return compute_trends(user.id)

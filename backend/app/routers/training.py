"""Training plan endpoints — generation, retrieval, adaptation."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, get_current_user
from app.core.supabase import get_supabase_admin
from app.services.plan_generator import (
    PHILOSOPHIES,
    RACE_TYPES,
    generate_plan,
)

router = APIRouter(prefix="/training", tags=["training"])

RaceType = Literal["5k", "10k", "half_marathon", "marathon", "ultra", "triathlon", "general_fitness"]
Philosophy = Literal[
    "daniels", "hansons", "pfitzinger", "norwegian", "polarized", "lydiard", "auto_hybrid",
]


class PlanRequest(BaseModel):
    race_type: RaceType
    race_date: date = Field(description="When the race is — ISO date.")
    target_time_seconds: int | None = Field(default=None, ge=600, le=72000)
    philosophy: Philosophy = "auto_hybrid"
    start_date: date | None = Field(default=None, description="When training starts; defaults to tomorrow.")
    expand_first_n_weeks: int = Field(default=4, ge=1, le=12)


@router.post("/plan")
def create_plan(
    body: PlanRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    """Generate a periodized training plan using the configured LLM.

    Process:
      1. Pull the athlete's 12-week snapshot + latest limiter call.
      2. Stage 1 — generate the plan blueprint (phases, volume, principles).
      3. Stage 2 — expand the first N weeks into daily sessions.
      4. Persist plan + sessions, mark any previous plan paused.
    """
    if body.race_type not in RACE_TYPES:
        raise HTTPException(status_code=400, detail=f"race_type must be one of {RACE_TYPES}")
    if body.philosophy not in PHILOSOPHIES:
        raise HTTPException(status_code=400, detail=f"philosophy must be one of {PHILOSOPHIES}")

    try:
        result = generate_plan(
            user_id=user.id,
            race_type=body.race_type,
            race_date=body.race_date,
            target_time_seconds=body.target_time_seconds,
            philosophy=body.philosophy,
            start_date=body.start_date,
            expand_first_n_weeks=body.expand_first_n_weeks,
        )
    except RuntimeError as exc:
        # Missing LLM credentials — surface a clean 503.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return result


@router.get("/plan/current")
def get_current_plan(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict:
    """Return the user's active plan + the next 14 days of sessions."""
    client = get_supabase_admin()
    plans = (
        client.table("training_plans")
        .select("*")
        .eq("user_id", user.id)
        .eq("status", "active")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not plans:
        return {"active": False}
    plan = plans[0]

    today = date.today().isoformat()
    upcoming = (
        client.table("planned_workouts")
        .select("scheduled_date, session_type, sport, duration_min, distance_m, description, intensity_zones, rationale, status")
        .eq("plan_id", plan["id"])
        .gte("scheduled_date", today)
        .order("scheduled_date")
        .limit(14)
        .execute()
        .data
        or []
    )
    return {
        "active": True,
        "plan_id": plan["id"],
        "race_type": plan["race_type"],
        "race_date": plan.get("race_date"),
        "target_time_seconds": plan.get("target_time_seconds"),
        "philosophy": plan["philosophy"],
        "current_phase": plan.get("current_phase"),
        "weeks": plan["weeks"],
        "blueprint": (plan.get("plan_json") or {}).get("blueprint"),
        "next_14_days": upcoming,
    }

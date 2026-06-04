"""Training plan retrieval.

V1 deliberately has no in-app plan generator — the chat assistant writes
plans and persists them via the `save-training-plan` MCP tool. This
router just surfaces the active plan + next 14 days so the dashboard
and training page can render it.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user
from app.core.supabase import get_supabase_admin

router = APIRouter(prefix="/training", tags=["training"])


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
        .select(
            "scheduled_date, session_type, sport, duration_min, distance_m, description, intensity_zones, rationale, status"
        )
        .eq("user_id", user.id)
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

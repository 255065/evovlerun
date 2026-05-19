"""Plan CRUD tools — push and delete planned workouts.

Chirona-equivalent surface. Claude/ChatGPT uses these to add or remove
individual sessions from the user's active plan without going through the
full plan_generator (which only runs at race-setup time).

push lets the assistant slot in an ad-hoc session ("add a 6 km easy on
Tuesday"). delete removes a session by id.
"""

from datetime import date
from typing import Any

from app.core.supabase import get_supabase_admin
from mcp_server.context import get_user_id


VALID_SESSION_TYPES = (
    "easy", "long", "tempo", "threshold", "intervals", "vo2max",
    "fartlek", "hills", "recovery", "race", "strength",
    "cross_training", "rest",
)


def push_planned_workout(
    scheduled_date: str,
    session_type: str,
    sport: str = "running",
    duration_min: int = None,
    distance_m: int = None,
    description: str = None,
    rationale: str = None,
) -> dict[str, Any]:
    """Add a planned workout to the user's active training plan.

    Use this when the athlete asks the assistant to slot in an extra session
    ("add a 6 km easy run Tuesday at 6am", "schedule a tempo this Thursday").
    The session is attached to the currently active training plan, or created
    standalone if none exists.

    Args:
        scheduled_date: ISO date YYYY-MM-DD.
        session_type:   easy / long / tempo / threshold / intervals / vo2max /
                        fartlek / hills / recovery / race / strength /
                        cross_training / rest
        sport:          running / cycling / swimming / strength / walking /
                        hiking / other. Default running.
        duration_min:   Estimated duration in minutes.
        distance_m:     Target distance in meters.
        description:    Concrete prescription, e.g. "8x400m @ 3:30/km".
        rationale:      Why this session — the explainability the athlete sees.
    """
    user_id = get_user_id()
    try:
        d = date.fromisoformat(scheduled_date)
    except ValueError as exc:
        return {"error": f"scheduled_date must be YYYY-MM-DD ({exc})"}

    if session_type not in VALID_SESSION_TYPES:
        return {
            "error": f"session_type must be one of {list(VALID_SESSION_TYPES)}",
        }

    client = get_supabase_admin()

    # Find the active plan, if any. We allow standalone sessions but prefer
    # to attach to a plan so the dashboard's plan view picks them up.
    active = (
        client.table("training_plans")
        .select("id")
        .eq("user_id", user_id)
        .eq("status", "active")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    plan_id = active[0]["id"] if active else None
    if plan_id is None:
        return {
            "error": "No active training plan — generate a plan first or set a placeholder.",
        }

    row = {
        "plan_id": plan_id,
        "user_id": user_id,
        "scheduled_date": d.isoformat(),
        "session_type": session_type,
        "sport": sport,
        "duration_min": duration_min,
        "distance_m": distance_m,
        "description": description,
        "rationale": rationale,
        "status": "scheduled",
        "ai_adjustments": [{"by": "assistant", "action": "added"}],
    }
    inserted = client.table("planned_workouts").insert(row).execute()
    new_id = inserted.data[0]["id"] if inserted.data else None
    return {
        "ok": True,
        "id": new_id,
        "scheduled_date": d.isoformat(),
        "session_type": session_type,
        "sport": sport,
        "plan_id": plan_id,
    }


def delete_planned_workout(workout_id: str) -> dict[str, Any]:
    """Remove a planned workout by id.

    Use this when the athlete asks the assistant to remove a session they
    no longer want to do, OR to overwrite the auto-generated plan with a
    different session for that day (delete first, then push).

    Args:
        workout_id: The UUID of the planned workout row.
    """
    user_id = get_user_id()
    client = get_supabase_admin()
    result = (
        client.table("planned_workouts")
        .delete()
        .eq("id", workout_id)
        .eq("user_id", user_id)
        .execute()
    )
    deleted = result.data or []
    if not deleted:
        return {"ok": False, "error": "Planned workout not found or not owned by user."}
    return {"ok": True, "deleted_id": workout_id}

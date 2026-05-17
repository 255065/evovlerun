"""Limiter tools — current limiter + history."""

from datetime import date, timedelta
from typing import Any

from app.core.supabase import get_supabase_admin
from mcp_server.context import get_user_id


def get_current_limiter() -> dict[str, Any]:
    """The most recent limiter determination from the AI engine.

    Returns the primary + secondary limiter, confidence score, structured
    evidence (key observations, supporting data points, physiology explanation),
    and the recommended training focus.

    Use this when reasoning about training direction or explaining why a
    specific session is prescribed.
    """
    user_id = get_user_id()
    client = get_supabase_admin()
    rows = (
        client.table("limiter_history")
        .select("*")
        .eq("user_id", user_id)
        .order("detected_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return {
            "available": False,
            "message": "No limiter analysis yet — call POST /limiter/analyze to run one.",
        }
    r = rows[0]
    ev = r.get("evidence") or {}
    return {
        "available": True,
        "detected_at": r["detected_at"],
        "primary_limiter": r["primary_limiter"],
        "secondary_limiter": r.get("secondary_limiter"),
        "confidence": float(r["confidence"]),
        "key_observations": ev.get("key_observations") or [],
        "supporting_data_points": ev.get("supporting_data_points") or [],
        "physiology_explanation": ev.get("physiology_explanation"),
        "alternative_considered": ev.get("alternative_considered"),
        "recommended_focus": r.get("recommended_focus"),
    }


def get_limiter_history(days: int = 180) -> dict[str, Any]:
    """All limiter calls in a window — useful to see whether the athlete's
    limiter has shifted over time (e.g. as base-building addresses aerobic
    capacity, the limiter rotates to muscular endurance).

    Args:
        days: Lookback window. Default 180.
    """
    user_id = get_user_id()
    since = (date.today() - timedelta(days=days)).isoformat()
    client = get_supabase_admin()
    rows = (
        client.table("limiter_history")
        .select("detected_at, primary_limiter, secondary_limiter, confidence, recommended_focus")
        .eq("user_id", user_id)
        .gte("detected_at", since)
        .order("detected_at", desc=True)
        .execute()
        .data
        or []
    )
    return {
        "window_days": days,
        "count": len(rows),
        "history": [
            {
                "detected_at": r["detected_at"],
                "primary_limiter": r["primary_limiter"],
                "secondary_limiter": r.get("secondary_limiter"),
                "confidence": float(r["confidence"]),
                "recommended_focus": r.get("recommended_focus"),
            }
            for r in rows
        ],
    }

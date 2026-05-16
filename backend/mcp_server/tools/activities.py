"""Activity tools — list, get, training-volume aggregates."""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.supabase import get_supabase_admin
from mcp_server.context import get_user_id

# Valid sports for the `sport` argument. Kept as a plain str instead of a
# Literal so mcp 1.13's tool-introspection (which calls issubclass on every
# annotation) doesn't choke.
VALID_SPORTS = {"running", "cycling", "swimming", "strength", "walking", "hiking", "other", "all"}


def _activity_summary(row: dict[str, Any]) -> dict[str, Any]:
    """Trim Supabase row down to what Claude actually needs to reason."""
    pace = row.get("avg_pace_s_per_km")
    return {
        "id": row["id"],
        "source": row["source"],
        "sport": row["sport"],
        "started_at": row["started_at"],
        "duration_seconds": row["duration_seconds"],
        "duration_minutes": round(row["duration_seconds"] / 60, 1) if row.get("duration_seconds") else None,
        "distance_km": round(row["distance_m"] / 1000.0, 2) if row.get("distance_m") else None,
        "elevation_gain_m": row.get("elevation_gain_m"),
        "avg_hr": row.get("avg_hr"),
        "max_hr": row.get("max_hr"),
        "avg_pace_min_per_km": _format_pace(pace) if pace else None,
        "avg_power_w": row.get("avg_power_w"),
        "trimp": row.get("trimp"),
        "notes": row.get("notes"),
    }


def _format_pace(seconds_per_km: float) -> str:
    """3:45 instead of 225 seconds — humans read this, Claude reasons about it."""
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}/km"


def list_activities(
    days: int = 30,
    sport: str = "all",
    limit: int = 50,
) -> dict[str, Any]:
    """List the user's activities from the last `days` days.

    Args:
        days: How many days back to look. Default 30.
        sport: Filter by sport. One of: running, cycling, swimming, strength,
            walking, hiking, other, all. Default "all".
        limit: Cap on the number of activities returned. Default 50.

    Returns:
        {"activities": [...], "total": int, "window_days": int}
    """
    user_id = get_user_id()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    if sport not in VALID_SPORTS:
        sport = "all"

    client = get_supabase_admin()
    query = (
        client.table("workouts")
        .select("*")
        .eq("user_id", user_id)
        .gte("started_at", since)
        .order("started_at", desc=True)
        .limit(limit)
    )
    if sport != "all":
        query = query.eq("sport", sport)

    rows = query.execute().data or []
    return {
        "activities": [_activity_summary(r) for r in rows],
        "total": len(rows),
        "window_days": days,
    }


def get_activity(activity_id: str) -> dict[str, Any]:
    """Return the full record for a single activity, including raw provider data.

    Args:
        activity_id: UUID of the workout row.

    Returns:
        Full activity payload including raw provider response for splits/laps/etc.
    """
    user_id = get_user_id()
    client = get_supabase_admin()
    result = (
        client.table("workouts")
        .select("*")
        .eq("id", activity_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        return {"error": "Activity not found or not owned by this user"}

    row = result.data
    summary = _activity_summary(row)
    summary["raw_payload"] = row.get("raw_payload") or {}
    return summary


def get_training_volume(days: int = 7) -> dict[str, Any]:
    """Aggregate training volume for the user over the last N days.

    Args:
        days: Lookback window. Common values: 7 (weekly), 28 (4-week block), 84 (12-week macro).

    Returns:
        Totals + per-sport breakdown: distance, duration, sessions, avg HR, total elevation.
    """
    user_id = get_user_id()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    client = get_supabase_admin()
    rows = (
        client.table("workouts")
        .select("sport, duration_seconds, distance_m, elevation_gain_m, avg_hr, trimp")
        .eq("user_id", user_id)
        .gte("started_at", since)
        .execute()
        .data
        or []
    )

    total_sessions = len(rows)
    total_seconds = sum(r.get("duration_seconds") or 0 for r in rows)
    total_distance_m = sum(r.get("distance_m") or 0 for r in rows)
    total_elev = sum(r.get("elevation_gain_m") or 0 for r in rows)
    total_trimp = sum(r.get("trimp") or 0 for r in rows)

    per_sport: dict[str, dict[str, Any]] = {}
    for r in rows:
        s = r.get("sport") or "other"
        bucket = per_sport.setdefault(
            s,
            {"sessions": 0, "duration_minutes": 0, "distance_km": 0.0, "elevation_m": 0},
        )
        bucket["sessions"] += 1
        bucket["duration_minutes"] += round((r.get("duration_seconds") or 0) / 60, 1)
        bucket["distance_km"] += round((r.get("distance_m") or 0) / 1000.0, 2)
        bucket["elevation_m"] += r.get("elevation_gain_m") or 0

    return {
        "window_days": days,
        "total_sessions": total_sessions,
        "total_duration_hours": round(total_seconds / 3600, 2),
        "total_distance_km": round(total_distance_m / 1000.0, 2),
        "total_elevation_m": round(total_elev, 1),
        "total_trimp_proxy": round(total_trimp, 1) if total_trimp else None,
        "weekly_avg_distance_km": round((total_distance_m / 1000.0) / (days / 7), 2) if days >= 7 else None,
        "per_sport": per_sport,
    }

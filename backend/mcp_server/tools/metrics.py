"""MCP tools for derived metrics, trends, and post-workout AI briefings."""

from datetime import date, timedelta
from typing import Any

from app.core.supabase import get_supabase_admin
from app.services.trend_engine import compute_trends as svc_compute_trends
from mcp_server.context import get_user_id


def get_athlete_metrics() -> dict[str, Any]:
    """EvolveRun's derived performance metrics.

    Returns the most recent computed values: VDOT, VO2max (our estimate),
    threshold pace + HR, running-economy proxy, fatigue-resistance score
    (0-100), recovery-capacity score (0-100). Includes the inputs used so
    Claude can sanity-check the numbers.

    Use this when reasoning about training intensity, comparing fitness now
    vs earlier, or explaining why a session was prescribed.
    """
    user_id = get_user_id()
    client = get_supabase_admin()
    rows = (
        client.table("performance_profiles")
        .select(
            "snapshot_date, vdot, vo2max_evolverun, threshold_pace_s_per_km_evolverun, "
            "threshold_hr_evolverun, running_economy_s_per_km_per_bpm, "
            "fatigue_resistance_score, recovery_capacity_score, metrics_inputs"
        )
        .eq("user_id", user_id)
        .order("snapshot_date", desc=True)
        .limit(30)
        .execute()
        .data
        or []
    )
    # Coalesce: take latest non-null per field across recent rows.
    latest: dict[str, Any] = {}
    for r in rows:
        for k, v in r.items():
            if k == "metrics_inputs":
                continue
            if v is not None and latest.get(k) is None:
                latest[k] = v
    if not latest:
        return {"available": False, "message": "No metrics computed yet — trigger a Garmin sync."}

    latest["inputs"] = (rows[0] or {}).get("metrics_inputs") if rows else None
    return {"available": True, **latest}


def get_metric_trends() -> dict[str, Any]:
    """4 / 8 / 12-week trend cards for every key metric.

    Each card has: current value, window average, % delta from start of window,
    direction (up/down/flat), and whether the direction is good for that metric
    (HRV up = good, resting HR up = bad).

    Use this when the athlete asks "am I getting fitter?" or to ground claims
    about progression in actual data.
    """
    return svc_compute_trends(get_user_id())


def get_post_workout_briefings(days: int = 14) -> dict[str, Any]:
    """Recent AI-generated post-workout analyses for key sessions.

    Each briefing has: verdict (on_target/above/below/aborted), summary, what
    went well, watch-outs, physiological takeaway, and the recommended
    adjustment for the next similar session.

    Args:
        days: Lookback window. Default 14.
    """
    user_id = get_user_id()
    since = (date.today() - timedelta(days=days)).isoformat()
    client = get_supabase_admin()
    rows = (
        client.table("coach_briefings")
        .select("id, for_date, summary, body, reasoning, workout_id, created_at, model_used")
        .eq("user_id", user_id)
        .eq("briefing_type", "post_workout")
        .gte("for_date", since)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    return {
        "window_days": days,
        "count": len(rows),
        "briefings": [
            {
                "id": r["id"],
                "for_date": r["for_date"],
                "workout_id": r.get("workout_id"),
                "model": r.get("model_used"),
                "verdict": (r.get("reasoning") or {}).get("verdict"),
                "summary": r["summary"],
                "what_went_well": (r.get("reasoning") or {}).get("what_went_well") or [],
                "watch_outs": (r.get("reasoning") or {}).get("watch_outs") or [],
                "physiological_takeaway": (r.get("reasoning") or {}).get("physiological_takeaway"),
                "next_session_adjustment": (r.get("reasoning") or {}).get("next_session_adjustment"),
            }
            for r in rows
        ],
    }

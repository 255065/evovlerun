"""Recovery tools — sleep, HRV, body battery, readiness."""

from datetime import date, timedelta
from typing import Any

from app.core.supabase import get_supabase_admin
from mcp_server.context import get_user_id


def _row_to_metric(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": row["metric_date"],
        "resting_hr": row.get("resting_hr"),
        "hrv_rmssd": row.get("hrv_rmssd"),
        "sleep_hours": round(row["sleep_minutes"] / 60, 2) if row.get("sleep_minutes") else None,
        "sleep_score": row.get("sleep_score"),
        "readiness_score": row.get("readiness_score"),
        "body_battery": row.get("body_battery"),
        "weight_kg": row.get("weight_kg"),
    }


def get_recovery_snapshot() -> dict[str, Any]:
    """Snapshot of the user's most recent recovery state.

    Returns the latest daily_metrics row plus deltas vs. the 7-day average — so
    Claude can say "your HRV is 12% below your usual" without doing the math.
    """
    user_id = get_user_id()
    client = get_supabase_admin()
    rows = (
        client.table("daily_metrics")
        .select("*")
        .eq("user_id", user_id)
        .order("metric_date", desc=True)
        .limit(8)
        .execute()
        .data
        or []
    )
    if not rows:
        return {"available": False, "message": "No recovery data yet. Connect a wearable."}

    latest = _row_to_metric(rows[0])
    baseline_rows = rows[1:8]

    def avg(field: str) -> float | None:
        values = [r.get(field) for r in baseline_rows if r.get(field) is not None]
        return round(sum(values) / len(values), 2) if values else None

    baseline = {
        "resting_hr_7d_avg": avg("resting_hr"),
        "hrv_rmssd_7d_avg": avg("hrv_rmssd"),
        "sleep_minutes_7d_avg": avg("sleep_minutes"),
        "readiness_7d_avg": avg("readiness_score"),
    }

    def pct_delta(now: float | int | None, base: float | None) -> float | None:
        if now is None or base is None or base == 0:
            return None
        return round(((now - base) / base) * 100, 1)

    deltas = {
        "resting_hr_vs_7d_pct": pct_delta(latest["resting_hr"], baseline["resting_hr_7d_avg"]),
        "hrv_vs_7d_pct": pct_delta(latest["hrv_rmssd"], baseline["hrv_rmssd_7d_avg"]),
        "sleep_vs_7d_pct": (
            pct_delta(rows[0].get("sleep_minutes"), baseline["sleep_minutes_7d_avg"])
        ),
        "readiness_vs_7d_pct": pct_delta(latest["readiness_score"], baseline["readiness_7d_avg"]),
    }

    return {
        "available": True,
        "latest": latest,
        "baseline_7d": baseline,
        "deltas_pct": deltas,
    }


def get_sleep(days: int = 14) -> dict[str, Any]:
    """Sleep history for the last N days.

    Returns per-day sleep duration + score and a window average.
    """
    user_id = get_user_id()
    since = (date.today() - timedelta(days=days)).isoformat()

    client = get_supabase_admin()
    rows = (
        client.table("daily_metrics")
        .select("metric_date, sleep_minutes, sleep_score")
        .eq("user_id", user_id)
        .gte("metric_date", since)
        .order("metric_date", desc=True)
        .execute()
        .data
        or []
    )

    sessions = [
        {
            "date": r["metric_date"],
            "hours": round(r["sleep_minutes"] / 60, 2) if r.get("sleep_minutes") else None,
            "score": r.get("sleep_score"),
        }
        for r in rows
    ]
    durations = [s["hours"] for s in sessions if s["hours"] is not None]
    return {
        "window_days": days,
        "sessions": sessions,
        "avg_hours": round(sum(durations) / len(durations), 2) if durations else None,
        "nights_with_data": len(durations),
    }


def get_hrv_trend(days: int = 28) -> dict[str, Any]:
    """HRV (rMSSD) trend over the last N days.

    Returns per-day values + the 7-day rolling baseline so a coach can spot
    a 5%+ multi-day drop (a strong overtraining signal).
    """
    user_id = get_user_id()
    since = (date.today() - timedelta(days=days)).isoformat()

    client = get_supabase_admin()
    rows = (
        client.table("daily_metrics")
        .select("metric_date, hrv_rmssd")
        .eq("user_id", user_id)
        .gte("metric_date", since)
        .order("metric_date", desc=True)
        .execute()
        .data
        or []
    )

    series = [
        {"date": r["metric_date"], "rmssd": r.get("hrv_rmssd")}
        for r in rows
        if r.get("hrv_rmssd") is not None
    ]
    series_sorted = sorted(series, key=lambda x: x["date"])
    # 7-day rolling baseline
    baselined = []
    for i, point in enumerate(series_sorted):
        window = series_sorted[max(0, i - 6) : i + 1]
        avg = round(sum(p["rmssd"] for p in window) / len(window), 2)
        baselined.append({**point, "baseline_7d": avg})

    return {
        "window_days": days,
        "data_points": len(baselined),
        "series": list(reversed(baselined)),  # newest first
    }

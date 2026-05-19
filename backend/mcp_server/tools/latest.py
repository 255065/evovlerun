"""Latest-X point-lookups (Chirona-parity surface).

Three single-row reads — most recent run, most recent sleep, most recent
body composition. Claude/ChatGPT calls these for quick "show me my last X"
questions where the user doesn't care about history.
"""

from datetime import date, timedelta
from typing import Any

from app.core.supabase import get_supabase_admin
from mcp_server.context import get_user_id


def _format_pace(seconds_per_km: float | None) -> str | None:
    if not seconds_per_km:
        return None
    m, s = divmod(int(seconds_per_km), 60)
    return f"{m}:{s:02d}/km"


def _format_duration(total_seconds: int | None) -> str | None:
    if not total_seconds:
        return None
    h, rem = divmod(int(total_seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ---------------------------------------------------------------------------
# get_latest_run
# ---------------------------------------------------------------------------
def get_latest_run() -> dict[str, Any]:
    """Return the user's most recent running activity with key metrics.

    Includes distance, time, pace, HR (avg + max), cadence, power, elevation,
    aerobic/anaerobic training effect, cardiac drift, polarized score, and
    HR-zone breakdown when available. Use this for "show me my last run" /
    "how was today's run" style questions.
    """
    user_id = get_user_id()
    client = get_supabase_admin()
    rows = (
        client.table("workouts")
        .select(
            "id, source, started_at, distance_m, duration_seconds, "
            "avg_hr, max_hr, avg_pace_s_per_km, cadence_avg, avg_power_w, "
            "elevation_gain_m, aerobic_te, anaerobic_te, cardiac_drift_pct, "
            "pace_decay_pct, polarized_score, hr_zone_seconds, temperature_c, notes"
        )
        .eq("user_id", user_id)
        .eq("sport", "running")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return {"available": False, "message": "No running activities found."}
    r = rows[0]
    return {
        "available": True,
        "id": r["id"],
        "source": r["source"],
        "started_at": r["started_at"],
        "distance_km": round((r.get("distance_m") or 0) / 1000, 2),
        "duration_display": _format_duration(r.get("duration_seconds")),
        "duration_seconds": r.get("duration_seconds"),
        "avg_pace": _format_pace(r.get("avg_pace_s_per_km")),
        "avg_pace_s_per_km": r.get("avg_pace_s_per_km"),
        "avg_hr_bpm": r.get("avg_hr"),
        "max_hr_bpm": r.get("max_hr"),
        "cadence_spm": r.get("cadence_avg"),
        "avg_power_w": r.get("avg_power_w"),
        "elevation_gain_m": r.get("elevation_gain_m"),
        "aerobic_te": r.get("aerobic_te"),
        "anaerobic_te": r.get("anaerobic_te"),
        "cardiac_drift_pct": r.get("cardiac_drift_pct"),
        "pace_decay_pct": r.get("pace_decay_pct"),
        "polarized_score": r.get("polarized_score"),
        "hr_zone_seconds": r.get("hr_zone_seconds"),
        "temperature_c": r.get("temperature_c"),
        "notes": r.get("notes"),
    }


# ---------------------------------------------------------------------------
# get_latest_sleep
# ---------------------------------------------------------------------------
def get_latest_sleep() -> dict[str, Any]:
    """Return the user's most recent sleep night plus the 7-day baseline.

    Includes duration, sleep score, HRV (rMSSD), resting HR, readiness score,
    body battery, and SpO2 where available. Compares last night against the
    7-day rolling average so Claude can flag deviations.
    """
    user_id = get_user_id()
    client = get_supabase_admin()
    rows = (
        client.table("daily_metrics")
        .select(
            "metric_date, sleep_minutes, sleep_score, hrv_rmssd, "
            "resting_hr, readiness_score, body_battery, spo2_avg, "
            "respiration_avg"
        )
        .eq("user_id", user_id)
        .not_.is_("sleep_minutes", "null")
        .order("metric_date", desc=True)
        .limit(8)
        .execute()
        .data
        or []
    )
    if not rows:
        return {"available": False, "message": "No sleep data found."}

    latest = rows[0]
    prior = rows[1:8]   # up to 7 nights for the baseline

    def _avg(field: str) -> float | None:
        vals = [r[field] for r in prior if r.get(field) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    latest_minutes = latest.get("sleep_minutes")
    return {
        "available": True,
        "date": latest["metric_date"],
        "sleep_hours": round(latest_minutes / 60, 2) if latest_minutes else None,
        "sleep_score": latest.get("sleep_score"),
        "hrv_rmssd": latest.get("hrv_rmssd"),
        "resting_hr_bpm": latest.get("resting_hr"),
        "readiness_score": latest.get("readiness_score"),
        "body_battery": latest.get("body_battery"),
        "spo2_avg": latest.get("spo2_avg"),
        "respiration_avg": latest.get("respiration_avg"),
        "seven_day_baseline": {
            "sleep_hours": round(_avg("sleep_minutes") / 60, 2) if _avg("sleep_minutes") else None,
            "sleep_score": _avg("sleep_score"),
            "hrv_rmssd": _avg("hrv_rmssd"),
            "resting_hr_bpm": _avg("resting_hr"),
            "readiness_score": _avg("readiness_score"),
        },
    }


# ---------------------------------------------------------------------------
# get_latest_body
# ---------------------------------------------------------------------------
def get_latest_body() -> dict[str, Any]:
    """Return the user's most recent body composition snapshot.

    Pulls weight, body fat %, muscle mass from the latest profile and
    performance_profiles entries. When the user weighs in on a Garmin Index
    scale this is what shows up.
    """
    user_id = get_user_id()
    client = get_supabase_admin()

    # weight + body fat lands on profiles (latest measurement) and on
    # performance_profiles (snapshot per day). Coalesce across both.
    profile = (
        client.table("profiles")
        .select("weight_kg, height_cm, sex, date_of_birth, max_hr, resting_hr")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    pdata = profile.data if profile else {}

    perf = (
        client.table("performance_profiles")
        .select("snapshot_date, body_fat_pct, muscle_mass_kg")
        .eq("user_id", user_id)
        .not_.is_("body_fat_pct", "null")
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    body_row = perf[0] if perf else {}

    age = None
    if pdata.get("date_of_birth"):
        try:
            dob = date.fromisoformat(pdata["date_of_birth"])
            age = (date.today() - dob).days // 365
        except ValueError:
            pass

    return {
        "available": bool(pdata or body_row),
        "snapshot_date": body_row.get("snapshot_date"),
        "weight_kg": pdata.get("weight_kg"),
        "body_fat_pct": body_row.get("body_fat_pct"),
        "muscle_mass_kg": body_row.get("muscle_mass_kg"),
        "height_cm": pdata.get("height_cm"),
        "sex": pdata.get("sex"),
        "age_years": age,
        "max_hr_bpm": pdata.get("max_hr"),
        "resting_hr_bpm": pdata.get("resting_hr"),
    }

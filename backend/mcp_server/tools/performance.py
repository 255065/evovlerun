"""Performance baseline + personal records.

These tools surface Garmin's own physiological estimates (VO2max, LT, race
predictions, training status) so Claude can reason about the user's current
fitness ceiling without having to recompute everything from raw activities.
"""

from datetime import date, datetime, timedelta, timezone  # noqa: F401
from typing import Any

from app.core.supabase import get_supabase_admin
from mcp_server.context import get_user_id


def _format_pace(seconds_per_km: float | None) -> str | None:
    if not seconds_per_km:
        return None
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}/km"


def _format_race_time(seconds: int | None) -> str | None:
    if not seconds:
        return None
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def get_performance_baseline() -> dict[str, Any]:
    """Garmin's latest physiological estimates: VO2max, LT, race predictions,
    training status, endurance/hill scores, fitness age, FTP.

    Returns the most-recent `performance_profiles` row populated with Garmin
    fields. Use this when Claude needs to know what intensities are realistic
    for the user (e.g. "what's a realistic 10k goal time?") or when checking
    if the user is in a `productive` vs. `overreaching` state.
    """
    user_id = get_user_id()
    client = get_supabase_admin()
    result = (
        client.table("performance_profiles")
        .select("*")
        .eq("user_id", user_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    if not result.data:
        return {"available": False, "message": "No performance snapshot yet — trigger a Garmin sync."}

    p = result.data[0]
    return {
        "available": True,
        "snapshot_date": p.get("snapshot_date"),
        "vo2max": p.get("garmin_vo2max") or p.get("vo2max_estimated"),
        "lactate_threshold": {
            "hr": p.get("garmin_lt_hr") or p.get("lactate_threshold_hr"),
            "pace": _format_pace(p.get("garmin_lt_pace_s_per_km") or p.get("lactate_threshold_pace_s_per_km")),
            "pace_s_per_km": p.get("garmin_lt_pace_s_per_km") or p.get("lactate_threshold_pace_s_per_km"),
        },
        "race_predictions": {
            "5k": _format_race_time(p.get("race_prediction_5k_s")),
            "10k": _format_race_time(p.get("race_prediction_10k_s")),
            "half_marathon": _format_race_time(p.get("race_prediction_hm_s")),
            "marathon": _format_race_time(p.get("race_prediction_marathon_s")),
        },
        "training_status": p.get("garmin_training_status"),
        "training_load_focus": p.get("garmin_training_load_focus"),
        "endurance_score": p.get("garmin_endurance_score"),
        "hill_score": p.get("garmin_hill_score"),
        "fitness_age": p.get("garmin_fitness_age"),
        "running_tolerance": p.get("garmin_running_tolerance"),
        "ftp_w": p.get("ftp_w"),
        "body_composition": {
            "body_fat_pct": p.get("body_fat_pct"),
            "muscle_mass_kg": p.get("muscle_mass_kg"),
        },
    }


def get_personal_records() -> dict[str, Any]:
    """User's personal records from Garmin (best 5k, 10k, longest run, etc.).

    Returns records grouped by record_type, each with value, unit, and the
    activity it was set in.
    """
    user_id = get_user_id()
    client = get_supabase_admin()
    rows = (
        client.table("personal_records")
        .select("record_type, value, unit, achieved_at, activity_source_id, source")
        .eq("user_id", user_id)
        .order("achieved_at", desc=True)
        .execute()
        .data
        or []
    )

    formatted = []
    for r in rows:
        display: str | None = None
        if r.get("unit") == "s":
            display = _format_race_time(int(r["value"]))
        elif r.get("unit") == "m":
            display = f"{r['value']/1000:.2f} km"
        elif r.get("unit") == "w":
            display = f"{int(r['value'])} W"
        formatted.append({
            "record_type": r["record_type"],
            "value": r["value"],
            "unit": r.get("unit"),
            "display": display,
            "achieved_at": r.get("achieved_at"),
            "source": r.get("source"),
            "activity_source_id": r.get("activity_source_id"),
        })

    return {"count": len(formatted), "records": formatted}


def get_stress_trend(days: int = 14) -> dict[str, Any]:
    """Daily stress trend (Garmin all-day stress).

    Useful for spotting accumulated mental load that compounds with training
    load — high stress + high training load = elevated injury/illness risk.

    Args:
        days: Lookback window. Default 14.
    """
    user_id = get_user_id()
    since = (date.today() - timedelta(days=days)).isoformat()
    client = get_supabase_admin()
    rows = (
        client.table("daily_metrics")
        .select("metric_date, stress_avg, stress_max, body_battery, spo2_avg, respiration_avg")
        .eq("user_id", user_id)
        .gte("metric_date", since)
        .order("metric_date")
        .execute()
        .data
        or []
    )

    stress_vals = [r["stress_avg"] for r in rows if r.get("stress_avg")]
    avg = sum(stress_vals) / len(stress_vals) if stress_vals else None

    return {
        "window_days": days,
        "days_with_data": len(stress_vals),
        "window_avg_stress": round(avg, 1) if avg is not None else None,
        "daily": [
            {
                "date": r["metric_date"],
                "stress_avg": r.get("stress_avg"),
                "stress_max": r.get("stress_max"),
                "body_battery": r.get("body_battery"),
                "spo2_avg": r.get("spo2_avg"),
                "respiration_avg": r.get("respiration_avg"),
            }
            for r in rows
        ],
    }


def get_fitness_timeline(days: int = 90) -> dict[str, Any]:
    """Daily fitness (CTL) / fatigue (ATL) / form (TSB) / ACWR series.

    CTL = chronic training load (42-day EMA of daily TSS) — proxy for fitness.
    ATL = acute training load (7-day EMA) — recent fatigue.
    TSB = CTL - ATL — positive means fresh, negative means tired.
    ACWR = 7-day workload / (28-day workload / 4):
      < 0.8     detraining
      0.8–1.3   optimal sweet spot
      1.3–1.5   elevated injury risk
      > 1.5     danger zone

    Use this to spot training trends, detect when the user is overreaching,
    or judge whether they're ready for a hard block.

    Args:
        days: Lookback window. Default 90.
    """
    user_id = get_user_id()
    since = (date.today() - timedelta(days=days)).isoformat()
    client = get_supabase_admin()
    rows = (
        client.table("performance_profiles")
        .select("snapshot_date, fitness_ctl, fatigue_atl, form_tsb, acwr")
        .eq("user_id", user_id)
        .gte("snapshot_date", since)
        .order("snapshot_date")
        .execute()
        .data
        or []
    )

    if not rows:
        return {
            "available": False,
            "message": "No fitness timeline yet — trigger /performance/recompute first.",
        }

    latest = rows[-1]
    # Trend = today's CTL vs. 28 days ago.
    trend_pct = None
    if len(rows) >= 28:
        prev_ctl = rows[-28].get("fitness_ctl") or 0
        if prev_ctl:
            trend_pct = round((latest.get("fitness_ctl") - prev_ctl) / prev_ctl * 100, 1)

    def _zone(acwr):
        if acwr is None:
            return None
        if acwr < 0.8:
            return "detraining_or_undertrained"
        if acwr <= 1.3:
            return "optimal"
        if acwr <= 1.5:
            return "elevated_risk"
        return "high_injury_risk"

    return {
        "available": True,
        "window_days": days,
        "latest": {
            "date": latest["snapshot_date"],
            "fitness_ctl": latest.get("fitness_ctl"),
            "fatigue_atl": latest.get("fatigue_atl"),
            "form_tsb": latest.get("form_tsb"),
            "acwr": latest.get("acwr"),
            "acwr_zone": _zone(latest.get("acwr")),
        },
        "ctl_trend_28d_pct": trend_pct,
        "points": [
            {
                "date": r["snapshot_date"],
                "ctl": r.get("fitness_ctl"),
                "atl": r.get("fatigue_atl"),
                "tsb": r.get("form_tsb"),
                "acwr": r.get("acwr"),
            }
            for r in rows
        ],
    }


def get_zone_distribution(days: int = 28) -> dict[str, Any]:
    """Time-in-HR-zones across all workouts in a window.

    Returns total seconds per zone aggregated from each workout's
    `hr_zone_seconds`, plus a polarized-training compliance score
    (% of time in z1+z2 vs. z4+z5).

    Args:
        days: Lookback window. Default 28 (one mesocycle).
    """
    user_id = get_user_id()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    client = get_supabase_admin()
    rows = (
        client.table("workouts")
        .select("hr_zone_seconds, sport, started_at")
        .eq("user_id", user_id)
        .gte("started_at", since)
        .not_.is_("hr_zone_seconds", "null")
        .execute()
        .data
        or []
    )

    totals = {"z1": 0, "z2": 0, "z3": 0, "z4": 0, "z5": 0}
    for r in rows:
        zones = r.get("hr_zone_seconds") or {}
        for k, v in zones.items():
            if k in totals and isinstance(v, (int, float)):
                totals[k] += int(v)

    total = sum(totals.values())
    pct = {k: (round(v / total * 100, 1) if total else 0.0) for k, v in totals.items()}
    polarized_low = pct["z1"] + pct["z2"]
    polarized_high = pct["z4"] + pct["z5"]

    return {
        "window_days": days,
        "workouts_with_zones": len(rows),
        "total_seconds": total,
        "total_hours": round(total / 3600, 2),
        "per_zone_seconds": totals,
        "per_zone_pct": pct,
        "polarized": {
            "low_intensity_pct": round(polarized_low, 1),
            "high_intensity_pct": round(polarized_high, 1),
            "middle_pct": round(pct["z3"], 1),
            # Heuristic: >80% low + 10-20% high = compliant polarized.
            "is_polarized": polarized_low >= 75 and polarized_high >= 10,
        },
    }

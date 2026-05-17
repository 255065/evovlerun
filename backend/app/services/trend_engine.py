"""Trend analysis — compare key metrics across 4 / 8 / 12-week windows.

For each metric we return:
  current        the most recent value
  window_avg     the average of the entire window
  delta_pct      % change from window-start to current
  direction      "up" | "down" | "flat"
  better         True if the direction is a positive change for THIS metric
                 (some metrics are better when they go down, e.g. resting HR)

Backed by simple SQL aggregates over `performance_profiles`, `workouts`,
and `daily_metrics`. We don't need raw time-series in most cases — just
the windowed averages.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

from app.core.supabase import get_supabase_admin

Direction = Literal["up", "down", "flat"]
WINDOWS = (28, 56, 84)  # 4w, 8w, 12w


def compute_trends(user_id: str) -> dict[str, Any]:
    """Return trend cards for every key metric across all three windows."""
    client = get_supabase_admin()
    today = date.today()
    earliest = today - timedelta(days=max(WINDOWS) + 1)

    # ---- Pull once, slice in Python ----
    perf_rows = (
        client.table("performance_profiles")
        .select(
            "snapshot_date, fitness_ctl, fatigue_atl, form_tsb, acwr, "
            "vo2max_evolverun, vdot, threshold_pace_s_per_km_evolverun, "
            "threshold_hr_evolverun, running_economy_s_per_km_per_bpm, "
            "fatigue_resistance_score, recovery_capacity_score, garmin_vo2max"
        )
        .eq("user_id", user_id)
        .gte("snapshot_date", earliest.isoformat())
        .order("snapshot_date")
        .execute()
        .data
        or []
    )

    daily_rows = (
        client.table("daily_metrics")
        .select("metric_date, hrv_rmssd, resting_hr, sleep_score, readiness_score, stress_avg")
        .eq("user_id", user_id)
        .gte("metric_date", earliest.isoformat())
        .order("metric_date")
        .execute()
        .data
        or []
    )

    workout_rows = (
        client.table("workouts")
        .select("started_at, sport, source, distance_m, duration_seconds, hr_zone_seconds")
        .eq("user_id", user_id)
        .gte("started_at", (datetime.now(timezone.utc) - timedelta(days=max(WINDOWS) + 1)).isoformat())
        .execute()
        .data
        or []
    )

    # ---- Trend cards ----
    cards: list[dict[str, Any]] = []

    cards.append(_perf_trend("VO2max (EvolveRun)", perf_rows, "vo2max_evolverun", "up_is_better"))
    cards.append(_perf_trend("VO2max (Garmin)", perf_rows, "garmin_vo2max", "up_is_better"))
    cards.append(_perf_trend("VDOT", perf_rows, "vdot", "up_is_better"))
    cards.append(_perf_trend("Fitness (CTL)", perf_rows, "fitness_ctl", "up_is_better"))
    cards.append(_perf_trend("Form (TSB)", perf_rows, "form_tsb", "neutral"))
    cards.append(_perf_trend("Threshold pace", perf_rows, "threshold_pace_s_per_km_evolverun", "down_is_better"))
    cards.append(_perf_trend("Running economy", perf_rows, "running_economy_s_per_km_per_bpm", "down_is_better"))
    cards.append(_perf_trend("Fatigue resistance", perf_rows, "fatigue_resistance_score", "up_is_better"))
    cards.append(_perf_trend("Recovery capacity", perf_rows, "recovery_capacity_score", "up_is_better"))

    cards.append(_daily_trend("HRV (rMSSD)", daily_rows, "hrv_rmssd", "up_is_better"))
    cards.append(_daily_trend("Resting HR", daily_rows, "resting_hr", "down_is_better"))
    cards.append(_daily_trend("Sleep score", daily_rows, "sleep_score", "up_is_better"))
    cards.append(_daily_trend("Readiness", daily_rows, "readiness_score", "up_is_better"))
    cards.append(_daily_trend("Stress (avg)", daily_rows, "stress_avg", "down_is_better"))

    cards.append(_volume_trend("Weekly km (run)", workout_rows, sport="running"))
    cards.append(_polarized_trend("Z1-Z2 % of training time", workout_rows))

    # Drop cards with no data.
    cards = [c for c in cards if c.get("has_data")]
    return {"as_of": today.isoformat(), "cards": cards}


# ---------------------------------------------------------------------------
# Generic builders
# ---------------------------------------------------------------------------
def _perf_trend(label: str, rows: list[dict], col: str, polarity: str) -> dict[str, Any]:
    samples = [(r["snapshot_date"], r.get(col)) for r in rows]
    return _build_card(label, samples, polarity, unit_hint=col)


def _daily_trend(label: str, rows: list[dict], col: str, polarity: str) -> dict[str, Any]:
    samples = [(r["metric_date"], r.get(col)) for r in rows]
    return _build_card(label, samples, polarity, unit_hint=col)


def _volume_trend(label: str, workouts: list[dict], *, sport: str) -> dict[str, Any]:
    """Weekly distance in km, deduped Strava↔Garmin pairs."""
    # Bucket by ISO week.
    by_week: dict[str, dict[str, float]] = {}
    seen_keys: set[tuple] = set()
    for w in workouts:
        if w["sport"] != sport or not w.get("distance_m"):
            continue
        dt = datetime.fromisoformat(w["started_at"].replace("Z", "+00:00"))
        # Dedupe near-identical activities across providers.
        key = (dt.date().isoformat(), round(w["distance_m"] / 50))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        week_key = dt.date().isoformat()
        # Snap to the Monday of that week so we can compare windows cleanly.
        monday = dt.date() - timedelta(days=dt.weekday())
        bucket = by_week.setdefault(monday.isoformat(), {"km": 0.0})
        bucket["km"] += w["distance_m"] / 1000

    samples = [(k, v["km"]) for k, v in sorted(by_week.items())]
    return _build_card(label, samples, "up_is_better", unit_hint="km/week")


def _polarized_trend(label: str, workouts: list[dict]) -> dict[str, Any]:
    """% of run+ride time spent in z1+z2 per week."""
    by_week: dict[str, dict[str, int]] = {}
    for w in workouts:
        zones = w.get("hr_zone_seconds") or {}
        if not zones:
            continue
        dt = datetime.fromisoformat(w["started_at"].replace("Z", "+00:00"))
        monday = (dt.date() - timedelta(days=dt.weekday())).isoformat()
        bucket = by_week.setdefault(monday, {"easy": 0, "total": 0})
        easy = int(zones.get("z1") or 0) + int(zones.get("z2") or 0)
        total = sum(int(v) for v in zones.values() if isinstance(v, (int, float)))
        bucket["easy"] += easy
        bucket["total"] += total

    samples = []
    for week, b in sorted(by_week.items()):
        if b["total"] == 0:
            continue
        samples.append((week, round(b["easy"] / b["total"] * 100, 1)))
    return _build_card(label, samples, "up_is_better", unit_hint="% z1+z2")


# ---------------------------------------------------------------------------
# Trend-card builder
# ---------------------------------------------------------------------------
def _build_card(
    label: str,
    samples: list[tuple[str, float | None]],
    polarity: str,
    *,
    unit_hint: str | None = None,
) -> dict[str, Any]:
    # Clean nulls.
    clean = [(d, v) for d, v in samples if v is not None]
    card = {
        "metric": label,
        "polarity": polarity,
        "has_data": len(clean) >= 2,
        "unit_hint": unit_hint,
    }
    if not clean:
        return card

    latest_date, latest_value = clean[-1]
    card["current"] = round(float(latest_value), 2)
    card["latest_date"] = latest_date

    today = date.today()
    windows_out = {}
    for w_days in WINDOWS:
        window_start = today - timedelta(days=w_days)
        in_window = [(d, v) for d, v in clean if d >= window_start.isoformat()]
        if len(in_window) < 2:
            windows_out[f"{w_days // 7}w"] = None
            continue
        start_val = float(in_window[0][1])
        end_val = float(in_window[-1][1])
        avg_val = sum(float(v) for _, v in in_window) / len(in_window)
        delta_pct = ((end_val - start_val) / abs(start_val) * 100) if start_val else None
        if delta_pct is None:
            direction: Direction = "flat"
        elif abs(delta_pct) < 1.0:
            direction = "flat"
        else:
            direction = "up" if delta_pct > 0 else "down"
        better = _interpret_direction(direction, polarity)
        windows_out[f"{w_days // 7}w"] = {
            "samples": len(in_window),
            "window_avg": round(avg_val, 2),
            "start_value": round(start_val, 2),
            "end_value": round(end_val, 2),
            "delta_pct": round(delta_pct, 2) if delta_pct is not None else None,
            "direction": direction,
            "better": better,
        }
    card["windows"] = windows_out
    return card


def _interpret_direction(direction: Direction, polarity: str) -> bool | None:
    """Whether the direction is *good* given the metric's polarity."""
    if polarity == "neutral" or direction == "flat":
        return None
    if polarity == "up_is_better":
        return direction == "up"
    if polarity == "down_is_better":
        return direction == "down"
    return None

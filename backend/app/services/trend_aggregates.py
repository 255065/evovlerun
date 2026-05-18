"""Time-bucketed trend aggregates designed to look great as Claude charts.

These differ from the metric trends (trend_engine.py) in two ways:
  • Bucketed by month or week rather than by 4/8/12-week window
  • Returned in a chart-friendly shape: a `series` array of label+value rows,
    plus a `chart_hint` block that nudges Claude to render an artifact

The chart hint is intentionally explicit ("render as bar chart with line
overlay") because Claude's chart artifact triggers reliably when the
desired visualization is named in the data, not just hoped for.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.supabase import get_supabase_admin


def _format_pace(seconds_per_km: float | None) -> str | None:
    if not seconds_per_km:
        return None
    minutes = int(seconds_per_km // 60)
    seconds = int(seconds_per_km % 60)
    return f"{minutes}:{seconds:02d}/km"


def _month_label(d: date) -> str:
    return d.strftime("%b %Y")


# ---------------------------------------------------------------------------
# Easy run trend — pace + HR per month, the Chirona-style view
# ---------------------------------------------------------------------------
def easy_run_trend(*, user_id: str, months: int = 3) -> dict[str, Any]:
    """Average easy-run pace and HR for each of the last `months` months.

    "Easy" = a running activity where ≥60% of the time was spent in z1+z2.
    Dedupes Strava+Garmin twins by date+distance, preferring whichever row
    has zone data (Garmin).

    Returns a chart-ready payload: `series` with one entry per month, plus
    a `chart_hint` that explicitly asks for a bar+line chart so Claude's
    artifact renderer picks it up.
    """
    client = get_supabase_admin()
    today = date.today()

    # Window covers `months` full calendar months + the current partial month.
    start = (today.replace(day=1) - timedelta(days=32 * (months - 1))).replace(day=1)
    rows = (
        client.table("workouts")
        .select(
            "started_at, sport, source, distance_m, duration_seconds, "
            "avg_hr, avg_pace_s_per_km, hr_zone_seconds"
        )
        .eq("user_id", user_id)
        .eq("sport", "running")
        .gte("started_at", start.isoformat())
        .order("started_at")
        .execute()
        .data
        or []
    )

    # Dedupe near-duplicate Strava/Garmin pairs by (date, distance_to_100m).
    seen: dict[tuple, dict] = {}
    for r in rows:
        if not r.get("distance_m"):
            continue
        d = datetime.fromisoformat(r["started_at"].replace("Z", "+00:00")).date()
        key = (d.isoformat(), round(r["distance_m"] / 100))
        existing = seen.get(key)
        if not existing:
            seen[key] = r
        elif r.get("hr_zone_seconds") and not existing.get("hr_zone_seconds"):
            seen[key] = r   # prefer Garmin row that has zone data

    # Bucket by year-month.
    buckets: dict[str, list[dict]] = defaultdict(list)
    for r in seen.values():
        zones = r.get("hr_zone_seconds") or {}
        total_z = sum(v for v in zones.values() if isinstance(v, (int, float)))
        easy_z = (zones.get("z1") or 0) + (zones.get("z2") or 0)
        if total_z == 0:
            continue
        if easy_z / total_z < 0.6:
            continue        # not an easy run
        if not r.get("avg_pace_s_per_km") or not r.get("avg_hr"):
            continue
        d = datetime.fromisoformat(r["started_at"].replace("Z", "+00:00")).date()
        ym = f"{d.year}-{d.month:02d}"
        buckets[ym].append({
            "pace_s_per_km": float(r["avg_pace_s_per_km"]),
            "hr": int(r["avg_hr"]),
            "distance_km": round(r["distance_m"] / 1000, 2),
        })

    series = []
    for ym in sorted(buckets):
        runs = buckets[ym]
        avg_pace = sum(x["pace_s_per_km"] for x in runs) / len(runs)
        avg_hr = sum(x["hr"] for x in runs) / len(runs)
        y, m = ym.split("-")
        label = date(int(y), int(m), 1).strftime("%b")
        series.append({
            "month": label,
            "year_month": ym,
            "pace_s_per_km": round(avg_pace, 1),
            "pace_display": _format_pace(avg_pace),
            "hr_bpm": round(avg_hr, 1),
            "easy_runs": len(runs),
            "total_distance_km": round(sum(x["distance_km"] for x in runs), 1),
        })

    # Trend summary — compare first vs last month in the window.
    trend_text = None
    if len(series) >= 2:
        first, last = series[0], series[-1]
        pace_delta_s = last["pace_s_per_km"] - first["pace_s_per_km"]
        hr_delta = last["hr_bpm"] - first["hr_bpm"]
        if pace_delta_s < -2 and hr_delta < -1:
            trend_text = "Faster pace, lower easy HR — improving aerobic efficiency."
        elif pace_delta_s < -2 and hr_delta >= 0:
            trend_text = "Faster pace at similar HR — getting more efficient."
        elif pace_delta_s > 2 and hr_delta > 1:
            trend_text = "Slower pace and higher HR — possible fatigue accumulation."
        elif pace_delta_s > 2:
            trend_text = "Slightly slower pace — could be recovery weeks or warm weather."
        else:
            trend_text = "Pace and HR roughly stable."

    return {
        "title": "Easy run trend",
        "subtitle": f"{series[0]['month']} – {series[-1]['month']}" if series else None,
        "window_months": months,
        "metric": "pace_vs_hr",
        "series": series,
        "trend": trend_text,
        "chart_hint": {
            "type": "bar_with_line_overlay",
            "x_axis": "month",
            "bar_field": "pace_s_per_km",
            "bar_label_field": "pace_display",
            "line_field": "hr_bpm",
            "line_unit": "bpm",
            "description": (
                "Render this as a chart artifact: blue bars showing pace (lower is faster), "
                "an orange line showing average HR across the same months. Label each bar "
                "with its pace_display (e.g. 5:23/km) and each line point with the HR value."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Two-period comparison — week vs week or month vs month
# ---------------------------------------------------------------------------
def compare_periods(
    *,
    user_id: str,
    metric: str = "volume_km",
    weeks_back: int = 1,
) -> dict[str, Any]:
    """Compare the last N weeks against the equivalent prior block.

    Supported metrics:
      volume_km       — total running km
      sessions        — count of running sessions
      avg_easy_pace   — mean pace on easy-classified runs
      tss             — sum of training stress
      avg_hrv         — daily HRV mean
    """
    client = get_supabase_admin()
    now = datetime.now(timezone.utc)
    a_end = now
    a_start = a_end - timedelta(weeks=weeks_back)
    b_end = a_start
    b_start = b_end - timedelta(weeks=weeks_back)

    def stats(t_start: datetime, t_end: datetime) -> dict[str, Any]:
        workouts = (
            client.table("workouts")
            .select("sport, distance_m, duration_seconds, avg_hr, avg_pace_s_per_km, tss, hr_zone_seconds, started_at")
            .eq("user_id", user_id)
            .gte("started_at", t_start.isoformat())
            .lt("started_at", t_end.isoformat())
            .execute()
            .data
            or []
        )
        # Dedupe Strava/Garmin pairs
        seen: dict[tuple, dict] = {}
        for w in workouts:
            if not w.get("distance_m"):
                continue
            d = datetime.fromisoformat(w["started_at"].replace("Z", "+00:00")).date()
            key = (d.isoformat(), round(w["distance_m"] / 100))
            existing = seen.get(key)
            if not existing or (w.get("hr_zone_seconds") and not existing.get("hr_zone_seconds")):
                seen[key] = w
        rs = [w for w in seen.values() if w["sport"] == "running"]

        easy_paces = []
        for w in rs:
            z = w.get("hr_zone_seconds") or {}
            tot = sum(v for v in z.values() if isinstance(v, (int, float)))
            if tot and (z.get("z1", 0) + z.get("z2", 0)) / tot >= 0.6 and w.get("avg_pace_s_per_km"):
                easy_paces.append(float(w["avg_pace_s_per_km"]))

        # HRV daily mean from daily_metrics over the window.
        dm = (
            client.table("daily_metrics")
            .select("hrv_rmssd")
            .eq("user_id", user_id)
            .gte("metric_date", t_start.date().isoformat())
            .lt("metric_date", t_end.date().isoformat())
            .not_.is_("hrv_rmssd", "null")
            .execute()
            .data
            or []
        )
        hrv_vals = [r["hrv_rmssd"] for r in dm if r.get("hrv_rmssd")]

        return {
            "volume_km": round(sum((w.get("distance_m") or 0) for w in rs) / 1000, 2),
            "sessions": len(rs),
            "avg_easy_pace": round(sum(easy_paces) / len(easy_paces), 1) if easy_paces else None,
            "tss": round(sum((w.get("tss") or 0) for w in rs), 1),
            "avg_hrv": round(sum(hrv_vals) / len(hrv_vals), 1) if hrv_vals else None,
        }

    a = stats(a_start, a_end)
    b = stats(b_start, b_end)

    if metric not in a:
        raise ValueError(f"unknown metric {metric}")
    av = a[metric]
    bv = b[metric]
    delta_pct = None
    direction = "flat"
    if av is not None and bv is not None and bv != 0:
        delta_pct = round((av - bv) / bv * 100, 1)
        if metric == "avg_easy_pace":
            # Lower pace = faster, so reverse interpretation.
            direction = "faster" if av < bv - 2 else "slower" if av > bv + 2 else "flat"
        else:
            direction = "up" if av > bv else "down" if av < bv else "flat"

    return {
        "title": f"Last {weeks_back} week(s) vs prior {weeks_back} week(s)",
        "metric": metric,
        "current": {"value": av, "display": _display_metric(metric, av), "window": f"{a_start.date()} → {a_end.date()}"},
        "previous": {"value": bv, "display": _display_metric(metric, bv), "window": f"{b_start.date()} → {b_end.date()}"},
        "delta_pct": delta_pct,
        "direction": direction,
        "all_metrics": {
            "current": {k: _display_metric(k, v) for k, v in a.items()},
            "previous": {k: _display_metric(k, v) for k, v in b.items()},
        },
        "chart_hint": {
            "type": "side_by_side_bars",
            "description": (
                "Render as two grouped bars (current vs previous). Title the chart with "
                f"the metric name ({metric}). Use the delta_pct as a small badge."
            ),
        },
    }


def _display_metric(metric: str, value: Any) -> str | None:
    if value is None:
        return None
    if metric == "avg_easy_pace":
        return _format_pace(value)
    if metric == "volume_km":
        return f"{value} km"
    if metric == "sessions":
        return f"{int(value)} sessions"
    if metric == "tss":
        return f"{value} TSS"
    if metric == "avg_hrv":
        return f"{value} ms"
    return str(value)

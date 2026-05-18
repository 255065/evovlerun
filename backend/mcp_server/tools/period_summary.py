"""Period summary tool — Chirona-style compact aggregate over an activity window.

Returns a single text block matching Chirona's `get-period-summary` shape so
Claude renders it the same way. Parameters mirror Chirona exactly:
    startDate (YYYY-MM-DD)
    endDate   (YYYY-MM-DD)
    runOnly   (bool, optional) — filter to running activities only
    provider  (str,  optional) — "garmin", "strava", or "all" (default)

The returned string is intentionally human-readable. MCP outputs are strings
anyway, and putting the data in compact line-per-metric form makes Claude
either quote it back verbatim or feed it directly into a chart artifact.
"""

from collections import Counter
from datetime import date
from typing import Any

from app.core.supabase import get_supabase_admin
from mcp_server.context import get_user_id


def _format_pace(seconds_per_km: float | None) -> str | None:
    if not seconds_per_km:
        return None
    m, s = divmod(int(seconds_per_km), 60)
    return f"{m}:{s:02d}/km"


def _format_duration(total_seconds: int) -> str:
    h, rem = divmod(int(total_seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def get_period_summary(
    startDate: str,
    endDate: str,
    runOnly: bool = False,
    provider: str = "all",
) -> dict[str, Any]:
    """Aggregate stats for the user's activities in a date window.

    Use this when the athlete asks about a specific period — e.g. "how much
    did I run last month?", "summarise my last 6 weeks", "what was my total
    volume from Apr to May?". Returns counts, totals, and averages across
    distance, time, pace, HR, cadence, power, elevation, plus the longest
    single activity.

    Args:
        startDate: ISO date YYYY-MM-DD, inclusive.
        endDate:   ISO date YYYY-MM-DD, inclusive.
        runOnly:   When True, includes only running activities.
        provider:  "garmin" / "strava" / "all". "all" deduplicates
                   Strava↔Garmin twins by (date, distance).
    """
    user_id = get_user_id()

    # Validate dates up front so we fail with a clear message rather than
    # crashing on a malformed Supabase query.
    try:
        d_start = date.fromisoformat(startDate)
        d_end = date.fromisoformat(endDate)
    except ValueError as exc:
        return {"error": f"Invalid date — use YYYY-MM-DD. {exc}"}
    if d_start > d_end:
        return {"error": "startDate must be on or before endDate."}

    client = get_supabase_admin()
    query = (
        client.table("workouts")
        .select(
            "started_at, sport, source, distance_m, duration_seconds, "
            "avg_hr, avg_pace_s_per_km, avg_power_w, cadence_avg, "
            "elevation_gain_m, notes"
        )
        .eq("user_id", user_id)
        .gte("started_at", f"{startDate}T00:00:00")
        .lte("started_at", f"{endDate}T23:59:59")
    )
    if provider.lower() != "all":
        query = query.eq("source", provider.lower())
    if runOnly:
        query = query.eq("sport", "running")

    rows = query.order("started_at").execute().data or []

    # Dedupe Strava+Garmin pairs when provider=all. Key by date + 100m bucket
    # of distance — that catches twins reliably without collapsing legit
    # back-to-back sessions of the same distance.
    if provider.lower() == "all":
        seen: dict[tuple, dict] = {}
        for w in rows:
            dist_bucket = round((w.get("distance_m") or 0) / 100)
            key = (w["started_at"][:10], dist_bucket)
            existing = seen.get(key)
            if existing is None:
                seen[key] = w
                continue
            # Prefer the row with more enriched fields (Garmin typically wins).
            existing_score = sum(1 for k in ("avg_hr", "avg_power_w", "cadence_avg") if existing.get(k))
            new_score = sum(1 for k in ("avg_hr", "avg_power_w", "cadence_avg") if w.get(k))
            if new_score > existing_score:
                seen[key] = w
        rows = list(seen.values())

    if not rows:
        provider_label = provider.upper() if provider != "all" else "ALL"
        filter_label = " | runs only" if runOnly else ""
        return {
            "summary": (
                f"Period summary: {startDate} to {endDate} ({provider_label}){filter_label}\n"
                f"No activities found in this window."
            ),
            "count": 0,
        }

    # ---- Aggregates ----
    total_distance_m = sum((r.get("distance_m") or 0) for r in rows)
    total_duration_s = sum((r.get("duration_seconds") or 0) for r in rows)
    total_elev_m = sum((r.get("elevation_gain_m") or 0) for r in rows)
    longest_m = max((r.get("distance_m") or 0) for r in rows)

    # Weighted-by-distance pace average where pace exists.
    pace_pairs = [(r["avg_pace_s_per_km"], r.get("distance_m") or 0) for r in rows if r.get("avg_pace_s_per_km")]
    avg_pace = (sum(p * d for p, d in pace_pairs) / sum(d for _, d in pace_pairs)) if pace_pairs else None

    # Plain mean for HR / cadence / power (weighted-by-duration would be
    # nicer but the gain is marginal vs. complexity).
    hr_vals = [r["avg_hr"] for r in rows if r.get("avg_hr")]
    avg_hr = sum(hr_vals) / len(hr_vals) if hr_vals else None
    cad_vals = [r["cadence_avg"] for r in rows if r.get("cadence_avg")]
    avg_cadence = sum(cad_vals) / len(cad_vals) if cad_vals else None
    pow_vals = [r["avg_power_w"] for r in rows if r.get("avg_power_w")]
    avg_power = sum(pow_vals) / len(pow_vals) if pow_vals else None

    sport_counts = Counter(r["sport"] for r in rows)
    sport_breakdown = " ".join(f"{k} {v}" for k, v in sport_counts.most_common())

    # ---- Format Chirona-style block ----
    provider_label = provider.upper() if provider != "all" else "ALL"
    filter_label = " | runs only" if runOnly else ""
    lines = [
        f"Period summary: {startDate} to {endDate} ({provider_label}){filter_label}",
        f"Activities: {len(rows)}",
        f"Activity types: {sport_breakdown}",
        f"Total distance: {total_distance_m / 1000:.2f} km",
        f"Total time: {_format_duration(total_duration_s)}",
    ]
    if avg_pace:
        lines.append(f"Avg pace: {_format_pace(avg_pace)}")
    if avg_hr:
        lines.append(f"Avg HR: {round(avg_hr)} bpm")
    if avg_cadence:
        lines.append(f"Avg cadence: {round(avg_cadence)} spm")
    if avg_power:
        lines.append(f"Avg power: {round(avg_power)} W")
    if total_elev_m:
        lines.append(f"Total elevation: {round(total_elev_m)} m")
    lines.append(f"Longest: {longest_m / 1000:.2f} km")

    return {
        "summary": "\n".join(lines),
        "count": len(rows),
        "totals": {
            "distance_km": round(total_distance_m / 1000, 2),
            "duration_seconds": int(total_duration_s),
            "elevation_m": round(total_elev_m, 1),
            "longest_distance_km": round(longest_m / 1000, 2),
        },
        "averages": {
            "pace_display": _format_pace(avg_pace),
            "pace_s_per_km": round(avg_pace, 2) if avg_pace else None,
            "hr_bpm": round(avg_hr, 1) if avg_hr else None,
            "cadence_spm": round(avg_cadence, 1) if avg_cadence else None,
            "power_w": round(avg_power, 1) if avg_power else None,
        },
        "per_sport": dict(sport_counts),
        "filters": {
            "startDate": startDate,
            "endDate": endDate,
            "runOnly": runOnly,
            "provider": provider,
        },
    }

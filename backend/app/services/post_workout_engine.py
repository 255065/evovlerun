"""Automatic post-workout analysis for key sessions.

Runs after a sync detects new workouts. For each "key session" (long run,
intervals, threshold, tempo, race) we hit the LLM with:
  • The workout summary + splits + zone distribution + decoupling
  • The planned session it executed (if any)
  • Recent context: last 7 days CTL/ATL/TSB, current limiter
  • The athlete's thresholds (max HR, LT HR, LT pace)

The model returns a structured briefing: hit-the-target verdict, what went
well, what to watch, and one concrete adjustment for the next similar
session. Output lands in `coach_briefings` with type `post_workout` and
`workout_id` pointed at the analyzed workout (idempotent: we never re-analyze
the same workout).
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.supabase import get_supabase_admin
from app.services.llm import get_llm

log = logging.getLogger(__name__)

# Session types that warrant an analysis. Easy/recovery runs aren't worth a
# Claude call — they're maintenance, not signal.
KEY_SESSION_HINTS = ("long", "interval", "tempo", "threshold", "race", "hill", "vo2max", "fartlek")


REPORT_TOOL_NAME = "report_workout_analysis"
REPORT_TOOL_DESC = (
    "Submit the post-workout analysis. Call this exactly once with your full "
    "assessment of the session."
)
REPORT_TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["verdict", "summary", "what_went_well", "watch_outs", "next_session_adjustment"],
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["on_target", "above_target", "below_target", "aborted"],
            "description": "How well the session matched its planned intent.",
        },
        "summary": {
            "type": "string",
            "description": "1-2 sentence executive summary of the session, including the key numbers.",
        },
        "what_went_well": {
            "type": "array",
            "items": {"type": "string"},
            "description": "1–3 specific positive observations citing the data.",
        },
        "watch_outs": {
            "type": "array",
            "items": {"type": "string"},
            "description": "1–3 specific concerns or warning signs (decoupling, pace decay, HR drift).",
        },
        "physiological_takeaway": {
            "type": "string",
            "description": "What this workout tells us about the athlete's fitness/limiter right now.",
        },
        "next_session_adjustment": {
            "type": "string",
            "description": "ONE concrete adjustment for the next similar session, citing this session's data.",
        },
    },
}

SYSTEM_PROMPT = """You are a sport scientist giving a focused post-workout debrief.

You'll see ONE recently-completed workout — its summary, splits, HR zones,
decoupling, and the planned session it was supposed to execute. You also see
the athlete's current limiter and recent context.

Tone:
  • Direct, evidence-citing, no fluff.
  • If something went well, cite the number. If something is concerning, cite the number.
  • Don't repeat the athlete's data back at them — interpret it.

Verdict guidance:
  • on_target      — hit the prescribed paces / durations / HR
  • above_target   — went harder/longer than prescribed (not always bad)
  • below_target   — fell short of prescribed intensity or duration
  • aborted        — workout cut short or fundamentally different from plan

Output: call `report_workout_analysis` exactly once. No prose."""


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def analyze_recent_workouts(*, user_id: str, since_hours: int = 48) -> dict[str, Any]:
    """Find key sessions in the last `since_hours` that haven't been analyzed,
    and run the post-workout AI on each. Idempotent.
    """
    client = get_supabase_admin()
    since = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()

    # Pull candidate workouts. We prefer Garmin over Strava when both exist
    # because Garmin carries the split + zone data.
    workouts = (
        client.table("workouts")
        .select("id, source, source_id, sport, started_at, notes, duration_seconds, distance_m, "
                "avg_hr, max_hr, hr_zone_seconds, cardiac_drift_pct, pace_decay_pct, polarized_score, "
                "aerobic_te, anaerobic_te, training_load, avg_pace_s_per_km, vo2max_at_activity")
        .eq("user_id", user_id)
        .gte("started_at", since)
        .order("started_at", desc=True)
        .execute()
        .data
        or []
    )

    # Skip non-key sessions and already-analyzed workouts.
    already = (
        client.table("coach_briefings")
        .select("workout_id")
        .eq("user_id", user_id)
        .eq("briefing_type", "post_workout")
        .not_.is_("workout_id", "null")
        .execute()
        .data
        or []
    )
    seen = {r["workout_id"] for r in already}

    candidates: list[dict] = []
    for w in workouts:
        if w["id"] in seen:
            continue
        if not _is_key_session(w):
            continue
        # Skip the Strava twin if we already have the Garmin one.
        candidates.append(w)

    candidates = _dedupe_provider_pairs(candidates)
    if not candidates:
        return {"analyzed": 0, "skipped_reason": "no new key sessions"}

    analyzed = []
    for w in candidates:
        try:
            result = analyze_workout(user_id=user_id, workout_id=w["id"])
            analyzed.append({"workout_id": w["id"], "verdict": result.get("verdict")})
        except Exception as exc:  # noqa: BLE001
            log.warning("post-workout analysis failed for %s: %s", w["id"], exc)
            analyzed.append({"workout_id": w["id"], "error": str(exc)})

    return {"analyzed": len(analyzed), "results": analyzed}


def analyze_workout(*, user_id: str, workout_id: str) -> dict[str, Any]:
    """Run the AI on one specific workout and persist the briefing. Idempotent
    (will refuse to re-analyze a workout that already has a briefing)."""
    client = get_supabase_admin()

    # Idempotency: bail if already analyzed.
    existing = (
        client.table("coach_briefings")
        .select("id")
        .eq("workout_id", workout_id)
        .eq("briefing_type", "post_workout")
        .limit(1)
        .execute()
        .data
        or []
    )
    if existing:
        return {"status": "already_analyzed", "briefing_id": existing[0]["id"]}

    workout = (
        client.table("workouts")
        .select("*")
        .eq("id", workout_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
        .data
    )
    if not workout:
        return {"status": "not_found"}

    inputs = _gather_workout_context(user_id=user_id, workout=workout)

    llm = get_llm("reasoning")
    user_msg = (
        "Analyze this workout and give the athlete a debrief.\n\n"
        "```json\n" + json.dumps(inputs, indent=2, default=str) + "\n```"
    )
    out = llm.call_tool(
        system=SYSTEM_PROMPT,
        user=user_msg,
        tool_name=REPORT_TOOL_NAME,
        tool_description=REPORT_TOOL_DESC,
        tool_schema=REPORT_TOOL_SCHEMA,
        max_tokens=4000,
    )
    result = out.arguments

    # Persist.
    body_lines = [result["summary"]]
    if result.get("what_went_well"):
        body_lines.append("\n**Det gik godt:**")
        body_lines.extend(f"• {x}" for x in result["what_went_well"])
    if result.get("watch_outs"):
        body_lines.append("\n**Pas på:**")
        body_lines.extend(f"• {x}" for x in result["watch_outs"])
    if result.get("physiological_takeaway"):
        body_lines.append(f"\n**Fysiologisk takeaway:** {result['physiological_takeaway']}")
    if result.get("next_session_adjustment"):
        body_lines.append(f"\n**Næste session:** {result['next_session_adjustment']}")

    insert = client.table("coach_briefings").insert({
        "user_id": user_id,
        "briefing_type": "post_workout",
        "for_date": date.today().isoformat(),
        "summary": result["summary"],
        "body": "\n".join(body_lines),
        "reasoning": result,
        "model_used": out.model,
        "workout_id": workout_id,
        "analysis_inputs": inputs,
    }).execute()

    return {
        "status": "ok",
        "briefing_id": insert.data[0]["id"] if insert.data else None,
        **result,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_key_session(workout: dict) -> bool:
    """Decide whether this workout is worth a Claude/MiniMax call.

    Heuristics (any of):
      • Notes/name contains a key-session keyword
      • Distance ≥ 15 km running
      • Anaerobic_te ≥ 3 (Garmin's anaerobic training effect)
      • Aerobic_te ≥ 4 (Garmin's aerobic training effect ≥ "highly improving")
      • High HR zone activity (z4+z5 ≥ 25% of total)
    """
    notes = (workout.get("notes") or "").lower()
    if any(hint in notes for hint in KEY_SESSION_HINTS):
        return True
    if workout.get("sport") == "running" and (workout.get("distance_m") or 0) >= 15000:
        return True
    if (workout.get("anaerobic_te") or 0) >= 3:
        return True
    if (workout.get("aerobic_te") or 0) >= 4:
        return True
    zones = workout.get("hr_zone_seconds") or {}
    total = sum(v for v in zones.values() if isinstance(v, (int, float)))
    if total:
        hard = (zones.get("z4") or 0) + (zones.get("z5") or 0)
        if hard / total >= 0.25:
            return True
    return False


def _dedupe_provider_pairs(workouts: list[dict]) -> list[dict]:
    """Strava + Garmin both ingest the same activity. Prefer Garmin (has splits)."""
    seen: dict[tuple, dict] = {}
    for w in workouts:
        key = (w["started_at"][:16], round((w.get("distance_m") or 0) / 50))
        existing = seen.get(key)
        if not existing:
            seen[key] = w
            continue
        # Prefer the source with hr_zone_seconds (i.e. Garmin enriched).
        if w.get("hr_zone_seconds") and not existing.get("hr_zone_seconds"):
            seen[key] = w
    return list(seen.values())


def _gather_workout_context(*, user_id: str, workout: dict) -> dict[str, Any]:
    """Assemble the JSON we send to the LLM."""
    client = get_supabase_admin()

    # Splits for this workout.
    splits = (
        client.table("workout_splits")
        .select("split_index, duration_s, distance_m, avg_hr, max_hr, avg_pace_s_per_km, avg_cadence, avg_power_w")
        .eq("workout_id", workout["id"])
        .order("split_index")
        .execute()
        .data
        or []
    )

    # Planned session for that date, if any.
    planned = (
        client.table("planned_workouts")
        .select("session_type, sport, duration_min, distance_m, description, intensity_zones, rationale")
        .eq("user_id", user_id)
        .eq("scheduled_date", workout["started_at"][:10])
        .limit(1)
        .execute()
        .data
        or []
    )

    # Recent performance context.
    perf = (
        client.table("performance_profiles")
        .select("fitness_ctl, fatigue_atl, form_tsb, acwr, garmin_vo2max, vo2max_evolverun, threshold_hr_evolverun")
        .eq("user_id", user_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
        .data
        or [{}]
    )[0]

    # Current limiter.
    limiter = (
        client.table("limiter_history")
        .select("primary_limiter, secondary_limiter, recommended_focus, confidence")
        .eq("user_id", user_id)
        .order("detected_at", desc=True)
        .limit(1)
        .execute()
        .data
        or [{}]
    )[0]

    # Profile thresholds.
    profile = (
        client.table("profiles")
        .select("max_hr, resting_hr, weight_kg, sex, date_of_birth")
        .eq("id", user_id)
        .maybe_single()
        .execute()
        .data
        or {}
    )

    return {
        "workout": {
            "id": workout["id"],
            "started_at": workout["started_at"],
            "sport": workout["sport"],
            "notes": workout.get("notes"),
            "duration_seconds": workout["duration_seconds"],
            "distance_km": round((workout.get("distance_m") or 0) / 1000, 2),
            "avg_hr": workout.get("avg_hr"),
            "max_hr": workout.get("max_hr"),
            "avg_pace_s_per_km": workout.get("avg_pace_s_per_km"),
            "hr_zone_seconds": workout.get("hr_zone_seconds"),
            "cardiac_drift_pct": workout.get("cardiac_drift_pct"),
            "pace_decay_pct": workout.get("pace_decay_pct"),
            "polarized_score": workout.get("polarized_score"),
            "aerobic_te": workout.get("aerobic_te"),
            "anaerobic_te": workout.get("anaerobic_te"),
            "training_load": workout.get("training_load"),
            "elevation_gain_m": workout.get("elevation_gain_m"),
            "temperature_c": workout.get("temperature_c"),
        },
        "splits": [
            {
                "i": s["split_index"],
                "dur_s": s.get("duration_s"),
                "dist_m": s.get("distance_m"),
                "avg_hr": s.get("avg_hr"),
                "pace_s_per_km": s.get("avg_pace_s_per_km"),
                "cadence": s.get("avg_cadence"),
                "power_w": s.get("avg_power_w"),
            }
            for s in splits
        ],
        "planned_session": planned[0] if planned else None,
        "current_performance": perf,
        "current_limiter": limiter,
        "athlete_profile": profile,
    }

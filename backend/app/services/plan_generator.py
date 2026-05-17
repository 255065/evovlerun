"""Training plan generator.

The plan-builder is the second AI module after limiter detection. It takes
the athlete's race goal + philosophy + current fitness + detected limiter and
generates a periodized training plan: phase structure, weekly volume targets,
and every individual session with rationale (the explainability promise from
CLAUDE.md).

We use the "reasoning" LLM tier — Sonnet / MiniMax-M2.5. Output is forced
through a tool schema so we get a structured plan ready to write into
`training_plans` + `planned_workouts`.

The generator works in TWO stages because a 12–20 week plan with daily
sessions is too long to fit in one tool call cleanly:

  Stage 1: Plan blueprint — phase structure, weekly volume curve, key
           workouts per phase, success metrics, rationale.

  Stage 2: Week-by-week expansion — for each week, generate 5–7 specific
           sessions with date, type, duration, distance, intensity zones,
           and per-session rationale.

This keeps each LLM call inside a manageable token budget and lets us re-run
stage 2 on a single week when the daily adapter kicks in.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any

from app.core.supabase import get_supabase_admin
from app.services.limiter_engine import gather_evidence
from app.services.llm import get_llm

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants & enums (mirror the DB CHECKs)
# ---------------------------------------------------------------------------
RACE_TYPES = ["5k", "10k", "half_marathon", "marathon", "ultra", "triathlon", "general_fitness"]
PHILOSOPHIES = ["daniels", "hansons", "pfitzinger", "norwegian", "polarized", "lydiard", "auto_hybrid"]
PHASES = ["base", "build", "peak", "taper", "race", "recovery"]
SESSION_TYPES = [
    "easy", "long", "tempo", "threshold", "intervals", "vo2max",
    "fartlek", "hills", "recovery", "race", "strength", "cross_training", "rest",
]
SPORTS = ["running", "cycling", "swimming", "strength", "walking", "hiking", "other"]


# ---------------------------------------------------------------------------
# Stage 1: blueprint
# ---------------------------------------------------------------------------
BLUEPRINT_TOOL_NAME = "submit_plan_blueprint"
BLUEPRINT_TOOL_DESC = (
    "Submit the high-level structure of the training plan. The detailed weekly "
    "sessions will be generated separately — focus on phases, volume curve, "
    "and the coaching rationale here."
)
BLUEPRINT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["total_weeks", "phases", "weekly_template", "guiding_principles", "key_metrics_to_track"],
    "properties": {
        "total_weeks": {
            "type": "integer",
            "minimum": 4,
            "maximum": 32,
            "description": "Total weeks from start date to race day.",
        },
        "phases": {
            "type": "array",
            "description": "Sequential training phases. Sum of week_count must equal total_weeks.",
            "items": {
                "type": "object",
                "required": ["name", "week_count", "weekly_volume_hours", "weekly_intensity_focus", "rationale"],
                "properties": {
                    "name": {"type": "string", "enum": PHASES},
                    "week_count": {"type": "integer", "minimum": 1},
                    "weekly_volume_hours": {
                        "type": "number",
                        "description": "Target weekly training hours during this phase.",
                    },
                    "weekly_intensity_focus": {
                        "type": "string",
                        "description": "What this phase targets (e.g. 'aerobic base, polarized 80/20', 'lactate threshold + race-specific work').",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Why this phase looks the way it does for THIS athlete (cite their limiter, fitness, etc).",
                    },
                },
            },
        },
        "weekly_template": {
            "type": "object",
            "description": (
                "Typical 7-day pattern showing how the week is structured. Use placeholders like "
                "'easy', 'long', 'threshold', 'rest'."
            ),
            "required": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            "properties": {
                "monday":    {"type": "string"},
                "tuesday":   {"type": "string"},
                "wednesday": {"type": "string"},
                "thursday":  {"type": "string"},
                "friday":    {"type": "string"},
                "saturday":  {"type": "string"},
                "sunday":    {"type": "string"},
            },
        },
        "guiding_principles": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3–5 coaching principles that drive every session prescription.",
        },
        "key_metrics_to_track": {
            "type": "array",
            "items": {"type": "string"},
            "description": "What signals will tell us the plan is working (e.g. 'threshold pace drop to <3:55/km', 'pace decay <3% on long runs').",
        },
        "auto_adapt_triggers": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Conditions that should make the daily adapter modify the plan (e.g. 'HRV -5% for 3 days → swap quality for easy z2').",
        },
    },
}


# ---------------------------------------------------------------------------
# Stage 2: weekly expansion
# ---------------------------------------------------------------------------
WEEK_TOOL_NAME = "submit_week_sessions"
WEEK_TOOL_DESC = (
    "Submit the daily sessions for ONE week of the plan. Every day in the week "
    "must be represented (use session_type=rest for off days). Honor the "
    "weekly volume target from the blueprint."
)
WEEK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["week_index", "phase", "sessions"],
    "properties": {
        "week_index": {"type": "integer", "minimum": 1},
        "phase": {"type": "string", "enum": PHASES},
        "weekly_summary": {
            "type": "string",
            "description": "1-2 sentence summary of this week's focus.",
        },
        "sessions": {
            "type": "array",
            "minItems": 7,
            "maxItems": 7,
            "items": {
                "type": "object",
                "required": ["day_offset", "session_type", "sport", "rationale"],
                "properties": {
                    "day_offset": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 6,
                        "description": "Days from the week's Monday. 0 = Monday, 6 = Sunday.",
                    },
                    "session_type": {"type": "string", "enum": SESSION_TYPES},
                    "sport": {"type": "string", "enum": SPORTS},
                    "duration_min": {
                        "type": "integer",
                        "description": "Estimated session duration. Omit for rest days.",
                    },
                    "distance_m": {
                        "type": "integer",
                        "description": "Target distance in meters. Omit when not applicable (rest, strength).",
                    },
                    "description": {
                        "type": "string",
                        "description": "Concrete session prescription, e.g. '8x800m @ 3:30/km with 2-min jog recovery'.",
                    },
                    "intensity_zones": {
                        "type": "object",
                        "description": "Target HR or pace zones. Free-form keys like z2_min, z2_max, target_pace_s_per_km.",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "WHY this specific session — the explainability for the athlete.",
                    },
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# System prompt — sport-scientist persona with strict output discipline
# ---------------------------------------------------------------------------
BLUEPRINT_SYSTEM = """You are an elite endurance coach (Daniels / Pfitzinger / Renato Canova background) building a periodized training plan for ONE specific athlete.

Inputs you'll receive:
  • Race goal: type, date, target time
  • Selected philosophy (or auto_hybrid — your choice)
  • Athlete snapshot: fitness, training history 84 days, race PRs vs predictions
  • Detected limiter from the limiter engine (PRIMARY signal for plan focus)

What "good" looks like:
  • Phases are calibrated to weeks-to-race AND the athlete's current fitness level. Don't prescribe an 8-week base if they have 12 weeks total — leave room for build/peak/taper.
  • Volume curve is realistic: a ~10% ramp per week max, with planned down-weeks every 3–4 weeks.
  • Intensity distribution reflects the philosophy:
      - polarized / norwegian: 75–85% z1-z2, 10–20% z4-z5, <10% z3
      - daniels: structured M-T-I-R sessions with specific paces
      - pfitzinger: medium-long runs + tempo emphasis
      - hansons: cumulative fatigue, capped long runs, high mileage
      - lydiard: large aerobic base, hill phase, sharpening
  • The plan ATTACKS the detected limiter. If anaerobic_capacity is the limiter, build in 2 weekly interval sessions. If muscular_endurance is the limiter, add progression long runs and race-specific workouts.
  • Every choice has a rationale. The athlete will see the "why" for every session.

Reasoning steps:
  1. Read the athlete snapshot. Note their current CTL, polarized status, limiter.
  2. Compute weeks available, place race day, choose phase boundaries.
  3. Pick philosophy if auto_hybrid — match athlete profile (e.g. polarized fits aerobic-strong runner with anaerobic limiter; pfitzinger fits threshold-focused).
  4. Set weekly volume hours per phase. Sanity-check against current training history.
  5. Design weekly template. Quality days separated by 48h, long run on weekend.
  6. Write rationales that reference SPECIFIC athlete data (their VO2max, their decoupling %, their limiter).

Output: call `submit_plan_blueprint` exactly once. No prose."""


WEEK_SYSTEM = """You are the same elite coach now expanding ONE week of the previously-generated plan blueprint into 7 specific daily sessions.

You'll receive:
  • The athlete snapshot (same as before)
  • The plan blueprint (phases, weekly template, principles)
  • Which week index this is + its phase

Rules:
  • Output EXACTLY 7 sessions, one per day (day_offset 0–6, Monday through Sunday).
  • Rest days: session_type=rest, omit duration_min and distance_m.
  • Quality sessions (threshold/intervals/vo2max/hills/race) must have at least 48h between them.
  • Every session needs a rationale that connects to the athlete's specific limiter or phase goal — not generic.
  • Honor the weekly volume target from the blueprint (sum of duration_min across non-rest days).
  • Use the athlete's current pace zones (from their lactate threshold pace or HM pace) when prescribing paces. Don't invent unrealistic targets.

Output: call `submit_week_sessions` exactly once. No prose."""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate_plan(
    *,
    user_id: str,
    race_type: str,
    race_date: date,
    target_time_seconds: int | None = None,
    philosophy: str = "auto_hybrid",
    start_date: date | None = None,
    expand_first_n_weeks: int = 4,
) -> dict[str, Any]:
    """Generate and persist a training plan for one athlete.

    Args:
        race_type: One of RACE_TYPES.
        race_date: Date the athlete races.
        target_time_seconds: Goal finish time in seconds (optional).
        philosophy: One of PHILOSOPHIES.
        start_date: When training starts. Defaults to tomorrow.
        expand_first_n_weeks: How many weeks to expand into detailed sessions
            up front. The rest can be expanded lazily by the daily adapter.

    Returns:
        Dict with the persisted plan id + blueprint + first N weeks of sessions.
    """
    if race_type not in RACE_TYPES:
        raise ValueError(f"race_type must be one of {RACE_TYPES}")
    if philosophy not in PHILOSOPHIES:
        raise ValueError(f"philosophy must be one of {PHILOSOPHIES}")

    start = start_date or (date.today() + timedelta(days=1))
    weeks_available = max(4, (race_date - start).days // 7)

    # 1) Snapshot — same evidence the limiter engine uses, plus latest limiter call.
    evidence = gather_evidence(user_id)
    latest_limiter = _load_latest_limiter(user_id)

    inputs = {
        "race_goal": {
            "race_type": race_type,
            "race_date": race_date.isoformat(),
            "target_time_seconds": target_time_seconds,
            "target_time_display": _fmt_secs(target_time_seconds) if target_time_seconds else None,
        },
        "philosophy": philosophy,
        "start_date": start.isoformat(),
        "weeks_available": weeks_available,
        "latest_limiter": latest_limiter,
        "athlete_snapshot": evidence,
    }

    # 2) Stage 1 — blueprint.
    llm = get_llm("reasoning")
    user_msg = (
        "Build the plan blueprint for this athlete.\n\n"
        "```json\n" + json.dumps(inputs, indent=2, default=str) + "\n```"
    )
    blueprint_result = llm.call_tool(
        system=BLUEPRINT_SYSTEM,
        user=user_msg,
        tool_name=BLUEPRINT_TOOL_NAME,
        tool_description=BLUEPRINT_TOOL_DESC,
        tool_schema=BLUEPRINT_SCHEMA,
        max_tokens=8000,
    )
    blueprint = blueprint_result.arguments

    # 3) Persist the parent training_plans row before expanding weeks so we
    #    have a plan_id to attach sessions to.
    plan_id = _persist_plan(
        user_id=user_id,
        race_type=race_type,
        race_date=race_date,
        target_time_seconds=target_time_seconds,
        philosophy=philosophy if philosophy != "auto_hybrid" else _infer_philosophy(blueprint),
        start_date=start,
        weeks=blueprint["total_weeks"],
        plan_json={
            "inputs": inputs,
            "blueprint": blueprint,
            "model": blueprint_result.model,
        },
    )

    # 4) Stage 2 — expand the first N weeks into daily sessions.
    expanded_weeks: list[dict[str, Any]] = []
    weeks_to_expand = min(expand_first_n_weeks, blueprint["total_weeks"])
    for week_idx in range(1, weeks_to_expand + 1):
        phase_name = _phase_for_week(blueprint["phases"], week_idx)
        week_user_msg = (
            f"Expand week {week_idx} of {blueprint['total_weeks']} (phase: {phase_name}).\n\n"
            "Athlete snapshot:\n```json\n"
            + json.dumps(evidence, indent=2, default=str)
            + "\n```\n\nPlan blueprint:\n```json\n"
            + json.dumps(blueprint, indent=2, default=str)
            + f"\n```\n\nThis is week_index={week_idx} of phase={phase_name}. "
            f"Week start date: {(start + timedelta(weeks=week_idx - 1)).isoformat()}."
        )
        week_result = llm.call_tool(
            system=WEEK_SYSTEM,
            user=week_user_msg,
            tool_name=WEEK_TOOL_NAME,
            tool_description=WEEK_TOOL_DESC,
            tool_schema=WEEK_SCHEMA,
            max_tokens=8000,
        )
        week_data = week_result.arguments
        _persist_week(
            plan_id=plan_id,
            user_id=user_id,
            week_start=start + timedelta(weeks=week_idx - 1),
            week_data=week_data,
        )
        expanded_weeks.append(week_data)

    return {
        "plan_id": plan_id,
        "model": blueprint_result.model,
        "weeks_available": weeks_available,
        "weeks_expanded": len(expanded_weeks),
        "blueprint": blueprint,
        "first_weeks": expanded_weeks,
        "tokens": {
            "blueprint_input": blueprint_result.input_tokens,
            "blueprint_output": blueprint_result.output_tokens,
        },
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fmt_secs(s: int | None) -> str | None:
    if not s:
        return None
    h, rem = divmod(int(s), 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def _load_latest_limiter(user_id: str) -> dict | None:
    client = get_supabase_admin()
    rows = (
        client.table("limiter_history")
        .select("primary_limiter, secondary_limiter, confidence, recommended_focus, evidence, detected_at")
        .eq("user_id", user_id)
        .order("detected_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return None
    r = rows[0]
    ev = r.get("evidence") or {}
    return {
        "detected_at": r["detected_at"],
        "primary_limiter": r["primary_limiter"],
        "secondary_limiter": r.get("secondary_limiter"),
        "confidence": float(r["confidence"]),
        "recommended_focus": r.get("recommended_focus"),
        "physiology_explanation": ev.get("physiology_explanation"),
    }


def _infer_philosophy(blueprint: dict) -> str:
    """If LLM chose auto_hybrid, sniff the most likely concrete philosophy from
    blueprint text. Defaults to 'polarized'."""
    text = json.dumps(blueprint).lower()
    for kw, ph in [
        ("polarized", "polarized"), ("norwegian", "norwegian"),
        ("pfitzinger", "pfitzinger"), ("hansons", "hansons"),
        ("daniels", "daniels"), ("lydiard", "lydiard"),
    ]:
        if kw in text:
            return ph
    return "polarized"


def _phase_for_week(phases: list[dict], week_idx: int) -> str:
    cumulative = 0
    for p in phases:
        cumulative += int(p["week_count"])
        if week_idx <= cumulative:
            return p["name"]
    return phases[-1]["name"]


def _persist_plan(
    *,
    user_id: str,
    race_type: str,
    race_date: date,
    target_time_seconds: int | None,
    philosophy: str,
    start_date: date,
    weeks: int,
    plan_json: dict,
) -> str:
    """Mark previous active plans as paused, then insert the new one."""
    client = get_supabase_admin()
    # Pause any currently-active plan for this user — we only run one at a time.
    client.table("training_plans").update({"status": "paused"}).eq(
        "user_id", user_id
    ).eq("status", "active").execute()
    # First-phase name must satisfy the DB CHECK constraint.
    first_phase = (plan_json.get("blueprint", {}).get("phases") or [{}])[0].get("name") or "base"
    if first_phase not in PHASES:
        first_phase = "base"

    insert = (
        client.table("training_plans")
        .insert({
            "user_id": user_id,
            "status": "active",
            "race_type": race_type,
            "race_date": race_date.isoformat(),
            "target_time_seconds": target_time_seconds,
            "philosophy": philosophy,
            "start_date": start_date.isoformat(),
            "weeks": int(weeks),
            "current_phase": first_phase,
            "plan_json": plan_json,
        })
        .execute()
    )
    return insert.data[0]["id"]


def _persist_week(
    *,
    plan_id: str,
    user_id: str,
    week_start: date,
    week_data: dict,
) -> None:
    """Write 7 planned_workouts rows for one expanded week.

    Some LLM providers occasionally return array items as JSON-encoded strings
    instead of nested objects. We parse string entries defensively so the
    plan-write doesn't crash on a single misbehaving response.
    """
    rows = []
    raw_sessions = week_data.get("sessions", [])
    sessions: list[dict] = []
    for s in raw_sessions:
        if isinstance(s, str):
            try:
                s = json.loads(s)
            except json.JSONDecodeError:
                log.warning("Skipping malformed session string in week_data: %s", s[:80])
                continue
        if not isinstance(s, dict):
            log.warning("Skipping non-dict session entry: %r", type(s).__name__)
            continue
        sessions.append(s)

    for s in sessions:
        day_offset = int(s.get("day_offset", 0))
        scheduled = week_start + timedelta(days=day_offset)
        sport = s.get("sport") or "running"
        session_type = s.get("session_type") or "easy"
        if session_type == "rest":
            rows.append({
                "plan_id": plan_id,
                "user_id": user_id,
                "scheduled_date": scheduled.isoformat(),
                "session_type": "rest",
                "sport": sport,
                "duration_min": None,
                "distance_m": None,
                "description": s.get("description") or "Rest day",
                "intensity_zones": s.get("intensity_zones") or {},
                "rationale": s.get("rationale"),
                "status": "scheduled",
            })
            continue
        rows.append({
            "plan_id": plan_id,
            "user_id": user_id,
            "scheduled_date": scheduled.isoformat(),
            "session_type": session_type,
            "sport": sport,
            "duration_min": s.get("duration_min"),
            "distance_m": s.get("distance_m"),
            "description": s.get("description"),
            "intensity_zones": s.get("intensity_zones") or {},
            "rationale": s.get("rationale"),
            "status": "scheduled",
        })

    if rows:
        get_supabase_admin().table("planned_workouts").insert(rows).execute()

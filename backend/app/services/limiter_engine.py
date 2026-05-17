"""Limiter detection engine.

Claude Opus 4.7 analyzes a structured snapshot of the athlete's training data
and identifies the primary physiological limiter — the system that's currently
holding back performance. Output is forced into a strict JSON schema and
written to `limiter_history` so we can track how the limiter shifts over time.

The seven limiter buckets follow the standard endurance-coaching taxonomy:

  aerobic_capacity     — VO2max ceiling (low fractional utilization)
  lactate_threshold    — % of VO2max sustainable (poor LT for given VO2max)
  muscular_endurance   — fatigue late in long efforts (the marathon "wall")
  running_economy      — high O2 cost per unit pace (biomechanical inefficiency)
  anaerobic_capacity   — poor short-interval / sprint capability
  recovery             — chronic HRV depression, poor sleep, accumulated fatigue
  neuromuscular        — cadence/stride/form issues, late-stage fatigue patterns

The engine is intentionally evidence-driven: every limiter must cite which
data points (decoupling %, zone distribution, ACWR, race-vs-prediction gaps,
HRV trend, etc.) support the call.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.supabase import get_supabase_admin
from app.services.llm import get_llm

log = logging.getLogger(__name__)


def _fmt_secs(s: float | int) -> str:
    """Render seconds as H:MM:SS / M:SS for human-readable race times."""
    s = int(s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"

# ---------------------------------------------------------------------------
# Tool schema — Claude is forced to call this so we get structured output.
# ---------------------------------------------------------------------------
LIMITER_OPTIONS = [
    "aerobic_capacity",
    "lactate_threshold",
    "muscular_endurance",
    "running_economy",
    "anaerobic_capacity",
    "recovery",
    "neuromuscular",
]

REPORT_TOOL_NAME = "report_limiter"
REPORT_TOOL_DESCRIPTION = (
    "Submit the limiter analysis. Call this exactly once with your final, "
    "fully-justified determination."
)
REPORT_TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["primary_limiter", "confidence", "evidence", "recommended_focus"],
    "properties": {
        "primary_limiter": {
            "type": "string",
            "enum": LIMITER_OPTIONS,
            "description": "The single biggest physiological constraint on current performance.",
        },
        "secondary_limiter": {
            # OpenAI/MiniMax don't like `null` inside enum — describe as optional string.
            "type": "string",
            "enum": LIMITER_OPTIONS,
            "description": "Optional second limiter that compounds with the primary. Omit if there is none.",
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Calibrated confidence in the primary determination. 0.5 = coin flip.",
        },
        "evidence": {
            "type": "object",
            "required": ["key_observations", "supporting_data_points", "physiology_explanation"],
            "properties": {
                "key_observations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "3–6 concrete observations from the data (e.g. 'aerobic decoupling +11.9% during CPH marathon')."
                    ),
                },
                "supporting_data_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific numbers cited — VO2max, decoupling %, ACWR, etc.",
                },
                "physiology_explanation": {
                    "type": "string",
                    "description": "1–2 paragraphs explaining the physiological mechanism in plain language.",
                },
                "alternative_considered": {
                    "type": "string",
                    "description": "What other limiter you considered and why you ruled it out.",
                },
            },
        },
        "recommended_focus": {
            "type": "string",
            "description": (
                "Concrete training prescription for the next 4–8 weeks (e.g. 'increase z1-z2 to >75% with 2 weekly threshold sessions')."
            ),
        },
    },
}


# ---------------------------------------------------------------------------
# System prompt — grounds Claude in sport science and tells it how to reason.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a senior endurance sport scientist analyzing one athlete's training data.

Your job: identify the single physiological system that is most limiting this athlete's performance right now, with the secondary system that compounds it. Be specific. Be evidence-based. Cite numbers.

Physiology taxonomy you must use:
  • aerobic_capacity — VO2max ceiling. Signs: low fractional utilization (race times worse than VO2max predicts), low CTL ceiling despite high training time.
  • lactate_threshold — % of VO2max the athlete can sustain. Signs: race times match VO2max prediction (no over-performance), threshold pace stagnant despite volume.
  • muscular_endurance — late-effort fatigue. Signs: high aerobic decoupling (>5% Friel) in long runs, pace decay in second half of marathons, "the wall" around km 30, drop in power output in second half of long rides.
  • running_economy — O2 cost per pace. Signs: very high VO2max but mediocre race times, high cadence variability, large pace difference between flat and varied terrain at same HR.
  • anaerobic_capacity — short, high-intensity capability. Signs: poor 1k/1mi PR relative to 10k/HM PRs, weak finishing kick, can't hold z5 for ≥2 min.
  • recovery — chronic stress overflow. Signs: HRV trending down >5% over 5+ days, RHR up, sleep score declining, poor TSB recovery between sessions.
  • neuromuscular — biomechanical inefficiency. Signs: cadence drops late in runs, stride length collapse, asymmetric form.

Reasoning approach:
  1. Read every section of the data carefully — don't anchor on the first salient number.
  2. Look for cross-confirmation: a limiter call should be supported by 2+ independent signals.
  3. Calibrate confidence honestly. If data is sparse or signals conflict, confidence ≤ 0.7.
  4. Prefer the limiter that produces the BIGGEST gain when addressed — not just the most obvious weakness.
  5. The "recommended_focus" must be specific (zone %, weekly sessions, weeks-to-reassess), not generic ("train more").
  6. When a recent race exists, weight its execution data heavily — race day reveals limiters that training masks.
  7. Account for context: post-race weeks show low ACWR for taper/recovery reasons, not detraining.

CRITICAL — interpreting race_performance_analysis:
  Each entry has `athlete_is_faster_by_pct`. Read it literally:
    > 0  → athlete PR is FASTER than prediction → OUTPERFORMS → this distance is a STRENGTH
    < 0  → athlete PR is SLOWER than prediction → UNDERPERFORMS → this distance is a LIMITER signal
  The `interpretation` field already spells this out — quote it directly. Do not invert the sign.
  An athlete who outperforms shorter distances but underperforms longer ones has a muscular-endurance / fatigue-resistance limiter, not a threshold limiter.

Output: call the `report_limiter` tool exactly once. Do not produce any other text."""


# ---------------------------------------------------------------------------
# Evidence assembly — pull all relevant data into one structured payload
# ---------------------------------------------------------------------------
def gather_evidence(user_id: str) -> dict[str, Any]:
    """Assemble the structured payload that goes to Claude.

    Pulls 12 weeks of training data + the latest performance snapshot +
    aggregated zone/recovery signals. Everything is computed-not-raw so we
    don't burn tokens on workout-by-workout dumps.
    """
    client = get_supabase_admin()
    today = date.today()
    since_dt = datetime.now(timezone.utc) - timedelta(days=84)

    # 1) Profile
    profile = (
        client.table("profiles")
        .select("date_of_birth, sex, height_cm, weight_kg, primary_sport, "
                "experience_level, resting_hr, max_hr, preferred_philosophy")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    profile_data = profile.data if profile else {}
    age = None
    if profile_data.get("date_of_birth"):
        try:
            dob = datetime.fromisoformat(profile_data["date_of_birth"]).date()
            age = (today - dob).days // 365
        except ValueError:
            pass

    # 2) Latest performance snapshot. We do this in two passes because the
    #    daily recompute writes CTL/ATL-only rows that null out Garmin's
    #    snapshot fields. Coalesce the most-recent values across the window.
    perf_rows = (
        client.table("performance_profiles")
        .select("*")
        .eq("user_id", user_id)
        .order("snapshot_date", desc=True)
        .limit(90)
        .execute()
        .data
        or []
    )
    perf: dict = {}
    if perf_rows:
        # Latest row = today's load. Then walk older rows to fill any nulls.
        perf = dict(perf_rows[0])
        for older in perf_rows[1:]:
            for k, v in older.items():
                if perf.get(k) is None and v is not None:
                    perf[k] = v

    # CTL trend (today vs. 28 days ago)
    trend_resp = (
        client.table("performance_profiles")
        .select("snapshot_date, fitness_ctl, fatigue_atl, form_tsb, acwr")
        .eq("user_id", user_id)
        .gte("snapshot_date", (today - timedelta(days=28)).isoformat())
        .order("snapshot_date")
        .execute()
    )
    trend_rows = trend_resp.data or []
    ctl_trend_pct = None
    if len(trend_rows) >= 2 and trend_rows[0].get("fitness_ctl"):
        first = trend_rows[0]["fitness_ctl"]
        last = trend_rows[-1]["fitness_ctl"]
        if first:
            ctl_trend_pct = round((last - first) / first * 100, 1)

    # 3) Workouts (last 84 days) — only summary stats, no raw rows
    wo_rows = (
        client.table("workouts")
        .select("sport, duration_seconds, distance_m, avg_hr, max_hr, trimp, tss, "
                "cardiac_drift_pct, pace_decay_pct, polarized_score, hr_zone_seconds, "
                "aerobic_te, anaerobic_te, notes, started_at, training_load")
        .eq("user_id", user_id)
        .gte("started_at", since_dt.isoformat())
        .order("started_at", desc=True)
        .execute()
        .data
        or []
    )

    # Aggregate zones across the whole window
    zone_totals = {"z1": 0, "z2": 0, "z3": 0, "z4": 0, "z5": 0}
    for w in wo_rows:
        zones = w.get("hr_zone_seconds") or {}
        for k, v in zones.items():
            if k in zone_totals and isinstance(v, (int, float)):
                zone_totals[k] += int(v)
    total_zone_seconds = sum(zone_totals.values())
    zone_pct = {
        k: (round(v / total_zone_seconds * 100, 1) if total_zone_seconds else 0)
        for k, v in zone_totals.items()
    }

    # Volume per sport
    per_sport: dict[str, dict] = {}
    for w in wo_rows:
        s = w.get("sport") or "other"
        b = per_sport.setdefault(s, {"sessions": 0, "duration_hours": 0.0, "distance_km": 0.0})
        b["sessions"] += 1
        b["duration_hours"] += round((w.get("duration_seconds") or 0) / 3600, 2)
        b["distance_km"] += round((w.get("distance_m") or 0) / 1000, 2)

    # Most recent races/long efforts where we have decoupling data.
    # wo_rows is already sorted desc by started_at, so just filter + cap.
    long_efforts = []
    seen_keys = set()
    for w in wo_rows:
        if (w.get("cardiac_drift_pct") is None) or (w.get("distance_m") or 0) < 15000:
            continue
        # Garmin + Strava both ingest the same activity — dedupe by date+distance.
        key = (w["started_at"][:10], round(w["distance_m"] / 100))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        long_efforts.append({
            "date": w["started_at"][:10],
            "sport": w["sport"],
            "distance_km": round(w["distance_m"] / 1000, 2),
            "duration_min": round(w["duration_seconds"] / 60),
            "avg_hr": w.get("avg_hr"),
            "cardiac_drift_pct": w.get("cardiac_drift_pct"),
            "pace_decay_pct": w.get("pace_decay_pct"),
            "polarized_score": w.get("polarized_score"),
            "aerobic_te": w.get("aerobic_te"),
            "training_load": w.get("training_load"),
            "notes": w.get("notes"),
        })
        if len(long_efforts) >= 6:
            break

    # 4) Personal records
    prs = (
        client.table("personal_records")
        .select("record_type, value, unit, achieved_at")
        .eq("user_id", user_id)
        .order("achieved_at", desc=True)
        .execute()
        .data
        or []
    )

    # 4b) Race PR vs Garmin prediction — explicit, pre-computed so the LLM
    #     can't flip the polarity. Convention:
    #       gap_pct > 0   athlete is FASTER than prediction (outperforms)
    #       gap_pct < 0   athlete is SLOWER than prediction (underperforms)
    pr_by_type = {r["record_type"]: r for r in prs}
    race_perf = []
    for distance, pr_key, pred_key in [
        ("5K",       "best_5k_s",       "race_prediction_5k_s"),
        ("10K",      "best_10k_s",      "race_prediction_10k_s"),
        ("HM",       "best_hm_s",       "race_prediction_hm_s"),
        ("Marathon", "best_marathon_s", "race_prediction_marathon_s"),
    ]:
        pr = pr_by_type.get(pr_key)
        pred = perf.get(pred_key)
        if not pr or not pred:
            continue
        pr_s = float(pr["value"])
        pred_s = float(pred)
        gap_seconds = pred_s - pr_s     # positive → PR faster than prediction
        gap_pct = round(gap_seconds / pred_s * 100, 2)
        if gap_pct > 2:
            interpretation = (
                f"OUTPERFORMS prediction by {gap_pct}% ({int(gap_seconds)}s faster). "
                f"This is a STRENGTH — lactate threshold and race execution exceed what "
                f"VO2max alone would predict. Look for limiters elsewhere."
            )
        elif gap_pct < -2:
            interpretation = (
                f"UNDERPERFORMS prediction by {-gap_pct}% ({int(-gap_seconds)}s slower). "
                f"Direct evidence of a limiter — race performance falls short of physiological ceiling."
            )
        else:
            interpretation = (
                f"MATCHES prediction within ±2% ({int(gap_seconds):+d}s). "
                f"Race performance aligns with VO2max-based expectation."
            )
        race_perf.append({
            "distance": distance,
            "athlete_pr_seconds": int(pr_s),
            "athlete_pr_display": _fmt_secs(pr_s),
            "garmin_prediction_seconds": int(pred_s),
            "garmin_prediction_display": _fmt_secs(pred_s),
            "athlete_vs_prediction_seconds": int(gap_seconds),
            "athlete_is_faster_by_pct": gap_pct,
            "interpretation": interpretation,
        })

    # 5) Recovery — last 14 days of daily metrics
    dm_rows = (
        client.table("daily_metrics")
        .select("metric_date, resting_hr, hrv_rmssd, sleep_minutes, sleep_score, "
                "readiness_score, stress_avg, spo2_avg, body_battery")
        .eq("user_id", user_id)
        .gte("metric_date", (today - timedelta(days=14)).isoformat())
        .order("metric_date")
        .execute()
        .data
        or []
    )
    hrv_vals = [r["hrv_rmssd"] for r in dm_rows if r.get("hrv_rmssd")]
    hrv_avg_7d = round(sum(hrv_vals[-7:]) / len(hrv_vals[-7:]), 1) if hrv_vals[-7:] else None
    hrv_avg_14d = round(sum(hrv_vals) / len(hrv_vals), 1) if hrv_vals else None
    hrv_trend_pct = (
        round((hrv_avg_7d - hrv_avg_14d) / hrv_avg_14d * 100, 1)
        if hrv_avg_7d and hrv_avg_14d else None
    )

    # 6) Assemble
    return {
        "as_of": today.isoformat(),
        "athlete": {
            "age": age,
            "sex": profile_data.get("sex"),
            "weight_kg": float(profile_data["weight_kg"]) if profile_data.get("weight_kg") else None,
            "height_cm": float(profile_data["height_cm"]) if profile_data.get("height_cm") else None,
            "primary_sport": profile_data.get("primary_sport"),
            "experience_level": profile_data.get("experience_level"),
            "resting_hr": profile_data.get("resting_hr"),
            "max_hr": profile_data.get("max_hr"),
            "preferred_philosophy": profile_data.get("preferred_philosophy"),
        },
        "current_fitness": {
            "vo2max": perf.get("garmin_vo2max") or perf.get("vo2max_estimated"),
            "lactate_threshold_hr": perf.get("garmin_lt_hr") or perf.get("lactate_threshold_hr"),
            "lactate_threshold_pace_s_per_km": perf.get("garmin_lt_pace_s_per_km") or perf.get("lactate_threshold_pace_s_per_km"),
            "ftp_w": perf.get("ftp_w"),
            "ctl": perf.get("fitness_ctl"),
            "atl": perf.get("fatigue_atl"),
            "tsb": perf.get("form_tsb"),
            "acwr": perf.get("acwr"),
            "ctl_trend_28d_pct": ctl_trend_pct,
            "garmin_training_status": perf.get("garmin_training_status"),
            "garmin_endurance_score": perf.get("garmin_endurance_score"),
            "garmin_hill_score": perf.get("garmin_hill_score"),
            "garmin_fitness_age": perf.get("garmin_fitness_age"),
        },
        # Pre-computed comparison — pre-baked so the LLM can't flip polarity.
        # Convention: athlete_is_faster_by_pct > 0 means PR is BETTER than prediction.
        "race_performance_analysis": race_perf,
        "personal_records": [
            {"type": r["record_type"], "value": r["value"], "unit": r.get("unit"),
             "date": r["achieved_at"][:10] if r.get("achieved_at") else None}
            for r in prs[:15]
        ],
        "training_volume_84d": {
            "total_sessions": len(wo_rows),
            "per_sport": per_sport,
            "hr_zone_distribution_pct": zone_pct,
            "is_polarized": (zone_pct.get("z1", 0) + zone_pct.get("z2", 0)) >= 75
                and (zone_pct.get("z4", 0) + zone_pct.get("z5", 0)) >= 10,
        },
        "long_efforts_with_decoupling": long_efforts,
        "recovery_14d": {
            "hrv_7d_avg": hrv_avg_7d,
            "hrv_14d_avg": hrv_avg_14d,
            "hrv_trend_pct_7d_vs_14d": hrv_trend_pct,
            "resting_hr_latest": dm_rows[-1].get("resting_hr") if dm_rows else None,
            "sleep_score_avg": round(
                sum(r.get("sleep_score") or 0 for r in dm_rows) / max(1, len([r for r in dm_rows if r.get("sleep_score")])),
                1,
            ) if dm_rows else None,
            "readiness_latest": dm_rows[-1].get("readiness_score") if dm_rows else None,
            "stress_avg_14d": round(
                sum(r.get("stress_avg") or 0 for r in dm_rows) / max(1, len([r for r in dm_rows if r.get("stress_avg")])),
                1,
            ) if dm_rows else None,
        },
    }


# ---------------------------------------------------------------------------
# Main detection call
# ---------------------------------------------------------------------------
def detect_limiter(*, user_id: str, persist: bool = True) -> dict[str, Any]:
    """Run the limiter analysis for one user.

    Uses whichever LLM is configured via `LLM_PROVIDER` (default anthropic).
    Returns the structured limiter call (whether or not we persisted it).
    """
    evidence = gather_evidence(user_id)
    user_message = (
        "Analyze the following athlete snapshot and identify the primary limiter.\n\n"
        "```json\n" + json.dumps(evidence, indent=2, default=str) + "\n```"
    )

    llm = get_llm("deep")
    out = llm.call_tool(
        system=SYSTEM_PROMPT,
        user=user_message,
        tool_name=REPORT_TOOL_NAME,
        tool_description=REPORT_TOOL_DESCRIPTION,
        tool_schema=REPORT_TOOL_SCHEMA,
        max_tokens=2000,
    )
    result = out.arguments

    if persist:
        _persist_limiter(user_id=user_id, result=result, evidence=evidence, model=out.model)

    return {
        "model": out.model,
        "stop_reason": out.stop_reason,
        "usage": {
            "input_tokens": out.input_tokens,
            "output_tokens": out.output_tokens,
        },
        "evidence_summary": {
            "sessions_84d": evidence["training_volume_84d"]["total_sessions"],
            "vo2max": evidence["current_fitness"]["vo2max"],
            "ctl": evidence["current_fitness"]["ctl"],
        },
        **result,
    }


def _persist_limiter(*, user_id: str, result: dict, evidence: dict, model: str) -> None:
    """Write the limiter call to `limiter_history` for trend tracking."""
    client = get_supabase_admin()
    client.table("limiter_history").insert({
        "user_id": user_id,
        "primary_limiter": result["primary_limiter"],
        "secondary_limiter": result.get("secondary_limiter"),
        "confidence": result["confidence"],
        "evidence": {
            **(result.get("evidence") or {}),
            "input_snapshot": evidence,
            "model": model,
        },
        "recommended_focus": result.get("recommended_focus"),
    }).execute()

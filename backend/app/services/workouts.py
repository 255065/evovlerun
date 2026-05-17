"""Helpers for writing normalized activities, daily metrics, performance
snapshots, splits and PRs into Supabase.

All upserts are idempotent so re-syncs don't duplicate data.
"""

from __future__ import annotations

from app.core.supabase import get_supabase_admin
from app.services.providers.base import (
    NormalizedActivity,
    NormalizedDailyMetric,
    NormalizedPerformanceSnapshot,
    NormalizedPersonalRecord,
)


# ---------------------------------------------------------------------------
# Workouts (+ splits)
# ---------------------------------------------------------------------------
def upsert_activities(*, user_id: str, activities: list[NormalizedActivity]) -> int:
    """Upsert a batch of activities and their splits.

    Returns the number of workout rows written. Splits are upserted in a
    follow-up call once we know the workout's id.
    """
    if not activities:
        return 0

    client = get_supabase_admin()
    rows = [_workout_row(user_id, a) for a in activities]
    result = (
        client.table("workouts")
        .upsert(rows, on_conflict="user_id,source,source_id")
        .execute()
    )

    # Splits: only those activities that have them, looked up by (source, source_id).
    activities_with_splits = [a for a in activities if a.splits]
    if activities_with_splits:
        _upsert_splits(user_id=user_id, activities=activities_with_splits)

    return len(result.data or rows)


def _workout_row(user_id: str, a: NormalizedActivity) -> dict:
    return {
        "user_id": user_id,
        "source": a.source,
        "source_id": a.source_id,
        "sport": a.sport,
        "started_at": a.started_at.isoformat(),
        "duration_seconds": a.duration_seconds,
        "distance_m": a.distance_m,
        "elevation_gain_m": a.elevation_gain_m,
        "avg_hr": a.avg_hr,
        "max_hr": a.max_hr,
        "avg_pace_s_per_km": a.avg_pace_s_per_km,
        "avg_power_w": a.avg_power_w,
        "normalized_power_w": a.normalized_power_w,
        "trimp": a.trimp,
        "tss": a.tss,
        "perceived_effort": a.perceived_effort,
        "notes": a.notes,
        "cadence_avg": a.cadence_avg,
        "cadence_max": a.cadence_max,
        "temperature_c": a.temperature_c,
        "calories": a.calories,
        "aerobic_te": a.aerobic_te,
        "anaerobic_te": a.anaerobic_te,
        "training_load": a.training_load,
        "hr_zone_seconds": a.hr_zone_seconds,
        "power_zone_seconds": a.power_zone_seconds,
        "cardiac_drift_pct": a.cardiac_drift_pct,
        "pace_decay_pct": a.pace_decay_pct,
        "polarized_score": a.polarized_score,
        "weather_payload": a.weather_payload,
        "vo2max_at_activity": a.vo2max_at_activity,
        "raw_payload": a.raw_payload,
    }


def _upsert_splits(*, user_id: str, activities: list[NormalizedActivity]) -> None:
    """Splits live in a child table — look up workout ids first, then upsert."""
    client = get_supabase_admin()

    # Map (source, source_id) → workout uuid in one round-trip.
    pairs = [(a.source, a.source_id) for a in activities]
    sources = list({s for s, _ in pairs})
    ids_query = (
        client.table("workouts")
        .select("id, source, source_id")
        .eq("user_id", user_id)
        .in_("source", sources)
        .in_("source_id", [sid for _, sid in pairs])
        .execute()
    )
    id_map = {(r["source"], r["source_id"]): r["id"] for r in (ids_query.data or [])}

    split_rows = []
    for a in activities:
        workout_id = id_map.get((a.source, a.source_id))
        if not workout_id:
            continue
        for s in a.splits:
            split_rows.append({
                "workout_id": workout_id,
                "user_id": user_id,
                "split_index": s.split_index,
                "split_type": s.split_type,
                "duration_s": s.duration_s,
                "distance_m": s.distance_m,
                "avg_hr": s.avg_hr,
                "max_hr": s.max_hr,
                "avg_pace_s_per_km": s.avg_pace_s_per_km,
                "avg_speed_mps": s.avg_speed_mps,
                "avg_cadence": s.avg_cadence,
                "avg_power_w": s.avg_power_w,
                "elevation_gain_m": s.elevation_gain_m,
                "intensity": s.intensity,
            })

    if split_rows:
        client.table("workout_splits").upsert(
            split_rows, on_conflict="workout_id,split_index"
        ).execute()


# ---------------------------------------------------------------------------
# Daily metrics
# ---------------------------------------------------------------------------
def upsert_daily_metrics(*, user_id: str, metrics: list[NormalizedDailyMetric]) -> int:
    """Upsert daily wellness rows. Dedup on (user_id, metric_date)."""
    if not metrics:
        return 0

    client = get_supabase_admin()
    rows = []
    for m in metrics:
        rows.append({
            "user_id": user_id,
            "metric_date": m.metric_date.isoformat(),
            "resting_hr": m.resting_hr,
            "hrv_rmssd": m.hrv_rmssd,
            "sleep_minutes": m.sleep_minutes,
            "sleep_score": m.sleep_score,
            "readiness_score": m.readiness_score,
            "body_battery": m.body_battery,
            "weight_kg": m.weight_kg,
            "body_temp_delta": m.body_temp_delta,
            "stress_avg": m.stress_avg,
            "stress_max": m.stress_max,
            "steps": m.steps,
            "floors_climbed": m.floors_climbed,
            "intensity_minutes_moderate": m.intensity_minutes_moderate,
            "intensity_minutes_vigorous": m.intensity_minutes_vigorous,
            "spo2_avg": m.spo2_avg,
            "spo2_min": m.spo2_min,
            "respiration_avg": m.respiration_avg,
            "respiration_min": m.respiration_min,
            "respiration_max": m.respiration_max,
            "body_fat_pct": m.body_fat_pct,
            "active_calories": m.active_calories,
            "total_calories": m.total_calories,
            "raw_payload": m.raw_payload,
        })

    client.table("daily_metrics").upsert(rows, on_conflict="user_id,metric_date").execute()
    return len(rows)


# ---------------------------------------------------------------------------
# Performance snapshots
# ---------------------------------------------------------------------------
def upsert_performance_snapshot(
    *, user_id: str, snapshot: NormalizedPerformanceSnapshot
) -> bool:
    """Upsert one day's performance snapshot from a provider.

    Writes into `performance_profiles` — only the Garmin-sourced columns plus
    the snapshot_date / user_id. Our own derived metrics (CTL, ATL, ACWR, etc.)
    are computed by the limiter engine in a separate pass.
    """
    if not snapshot:
        return False

    client = get_supabase_admin()
    client.table("performance_profiles").upsert({
        "user_id": user_id,
        "snapshot_date": snapshot.snapshot_date.isoformat(),
        "garmin_training_status": snapshot.garmin_training_status,
        "garmin_training_load_focus": snapshot.garmin_training_load_focus,
        "garmin_endurance_score": snapshot.garmin_endurance_score,
        "garmin_hill_score": snapshot.garmin_hill_score,
        "garmin_fitness_age": snapshot.garmin_fitness_age,
        "garmin_running_tolerance": snapshot.garmin_running_tolerance,
        "garmin_vo2max": snapshot.garmin_vo2max,
        "garmin_lt_hr": snapshot.garmin_lt_hr,
        "garmin_lt_pace_s_per_km": snapshot.garmin_lt_pace_s_per_km,
        "race_prediction_5k_s": snapshot.race_prediction_5k_s,
        "race_prediction_10k_s": snapshot.race_prediction_10k_s,
        "race_prediction_hm_s": snapshot.race_prediction_hm_s,
        "race_prediction_marathon_s": snapshot.race_prediction_marathon_s,
        "body_fat_pct": snapshot.body_fat_pct,
        "muscle_mass_kg": snapshot.muscle_mass_kg,
        "ftp_w": snapshot.ftp_w,
        # Mirror the Garmin values into our generic columns so existing tools
        # (and the limiter engine) read sensible defaults until our own model
        # is trained.
        "vo2max_estimated": snapshot.garmin_vo2max,
        "lactate_threshold_hr": snapshot.garmin_lt_hr,
        "lactate_threshold_pace_s_per_km": snapshot.garmin_lt_pace_s_per_km,
        "critical_power_w": snapshot.ftp_w,
        "notes": snapshot.raw_payload,
    }, on_conflict="user_id,snapshot_date").execute()
    return True


# ---------------------------------------------------------------------------
# Personal records
# ---------------------------------------------------------------------------
def upsert_personal_records(
    *, user_id: str, records: list[NormalizedPersonalRecord]
) -> int:
    if not records:
        return 0

    client = get_supabase_admin()
    rows = []
    for r in records:
        rows.append({
            "user_id": user_id,
            "source": r.source,
            "record_type": r.record_type,
            "value": r.value,
            "unit": r.unit,
            "achieved_at": r.achieved_at.isoformat() if r.achieved_at else None,
            "activity_source_id": r.activity_source_id,
            "raw_payload": r.raw_payload,
        })
    client.table("personal_records").upsert(
        rows, on_conflict="user_id,source,record_type,achieved_at"
    ).execute()
    return len(rows)

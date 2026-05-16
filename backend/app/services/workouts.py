"""Helpers for writing normalized activities and daily metrics into Supabase."""

from __future__ import annotations

from app.core.supabase import get_supabase_admin
from app.services.providers.base import NormalizedActivity, NormalizedDailyMetric


def upsert_activities(*, user_id: str, activities: list[NormalizedActivity]) -> int:
    """Upsert a batch of activities. Returns the number written.

    Deduplication uses (user_id, source, source_id) — matches the unique
    constraint on the workouts table.
    """
    if not activities:
        return 0

    client = get_supabase_admin()
    rows = []
    for a in activities:
        rows.append(
            {
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
                "raw_payload": a.raw_payload,
            }
        )

    client.table("workouts").upsert(rows, on_conflict="user_id,source,source_id").execute()
    return len(rows)


def upsert_daily_metrics(*, user_id: str, metrics: list[NormalizedDailyMetric]) -> int:
    """Upsert daily wellness rows. Dedup on (user_id, metric_date)."""
    if not metrics:
        return 0

    client = get_supabase_admin()
    rows = []
    for m in metrics:
        rows.append(
            {
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
                "raw_payload": m.raw_payload,
            }
        )

    client.table("daily_metrics").upsert(rows, on_conflict="user_id,metric_date").execute()
    return len(rows)

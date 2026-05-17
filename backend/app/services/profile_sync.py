"""Athlete-profile sync — populates `profiles.max_hr`, `resting_hr`, weight,
DOB, sex from the provider + observed workout data.

Why not just trust Garmin's `userMaxHr`?
  Garmin only sets that field if the user manually configured it. Most users
  never do — Connect auto-detects max HR from workouts. We do the same:
  the highest `max_hr` observed across the last 365 days of workouts is a
  more reliable max HR estimate than 220 - age.

Why merge instead of overwrite?
  We don't want to clobber values the user manually set in the app. We only
  fill blanks and update when the provider's value is clearly more recent or
  when our observed max_hr is higher than what's on file.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.supabase import get_supabase_admin
from app.services.providers.base import NormalizedAthleteProfile

log = logging.getLogger(__name__)


def sync_profile_from_provider(
    *,
    user_id: str,
    provider_profile: NormalizedAthleteProfile | None,
) -> dict[str, Any]:
    """Merge a provider profile + observed workout max_hr into `profiles`.

    Returns a summary of what was updated.
    """
    client = get_supabase_admin()

    # Pull what's already on the user's profile row so we don't overwrite
    # manually-set values with provider blanks.
    current_resp = (
        client.table("profiles")
        .select("date_of_birth, sex, height_cm, weight_kg, max_hr, resting_hr")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    current = current_resp.data if current_resp else {}

    update: dict[str, Any] = {}

    if provider_profile:
        # Only fill blanks for these — user might have edited them manually.
        if provider_profile.date_of_birth and not current.get("date_of_birth"):
            update["date_of_birth"] = provider_profile.date_of_birth.isoformat()
        if provider_profile.sex and not current.get("sex"):
            update["sex"] = provider_profile.sex
        if provider_profile.height_cm and not current.get("height_cm"):
            update["height_cm"] = provider_profile.height_cm

        # Weight changes naturally — always take the provider's latest reading
        # (Garmin sources this from the scale, which is the source of truth).
        if provider_profile.weight_kg:
            update["weight_kg"] = provider_profile.weight_kg

    # Observed max HR from the last 12 months of workouts.
    max_hr_observed = _max_hr_observed(user_id, days=365)
    existing_max = current.get("max_hr")
    if max_hr_observed:
        if not existing_max or max_hr_observed > existing_max:
            update["max_hr"] = int(max_hr_observed)

    # Resting HR — take the most recent non-null value from daily_metrics.
    rhr_recent = _latest_resting_hr(user_id, days=14)
    if rhr_recent:
        update["resting_hr"] = int(rhr_recent)

    if update:
        client.table("profiles").update(update).eq("id", user_id).execute()

    return {
        "fields_updated": list(update.keys()),
        "max_hr_observed": max_hr_observed,
        "max_hr_on_file_before": existing_max,
        "max_hr_on_file_after": update.get("max_hr") or existing_max,
        "resting_hr": rhr_recent,
    }


def _max_hr_observed(user_id: str, *, days: int = 365) -> int | None:
    """Highest max_hr field across the user's recent workouts.

    Filters out clearly bogus values (>225 = sensor glitch).
    """
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    client = get_supabase_admin()
    rows = (
        client.table("workouts")
        .select("max_hr")
        .eq("user_id", user_id)
        .gte("started_at", since)
        .not_.is_("max_hr", "null")
        .execute()
        .data
        or []
    )
    sane = [r["max_hr"] for r in rows if r.get("max_hr") and 120 <= r["max_hr"] <= 225]
    return max(sane) if sane else None


def _latest_resting_hr(user_id: str, *, days: int = 14) -> int | None:
    """Most recent non-null resting_hr from daily_metrics."""
    since = (date.today() - timedelta(days=days)).isoformat()
    client = get_supabase_admin()
    rows = (
        client.table("daily_metrics")
        .select("metric_date, resting_hr")
        .eq("user_id", user_id)
        .gte("metric_date", since)
        .not_.is_("resting_hr", "null")
        .order("metric_date", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    return rows[0]["resting_hr"] if rows else None

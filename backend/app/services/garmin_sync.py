"""High-level Garmin sync orchestrator.

Three sync modes:
  - `sync_full(user_id, days_back=90)` — backfill historical data
  - `sync_incremental(user_id)` — daily refresh (since last_sync_at)
  - `sync_activity_details(user_id, source_id)` — deep-enrich one activity

Each call writes whatever fields are available; missing fields stay NULL.
We don't fail the whole sync on a single endpoint error — Garmin's mobile
API is notoriously flaky.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from app.services.connections import load_tokens, mark_status
from app.services.metrics_engine import compute_all_metrics
from app.services.performance import recompute_for_user
from app.services.post_workout_engine import analyze_recent_workouts
from app.services.profile_sync import sync_profile_from_provider
from app.services.providers.base import ProviderAuthError, ProviderRateLimitError
from app.services.providers.garmin import GarminProvider
from app.services.workouts import (
    upsert_activities,
    upsert_daily_metrics,
    upsert_performance_snapshot,
    upsert_personal_records,
)

log = logging.getLogger(__name__)


class GarminSyncReport(dict):
    """Plain dict subclass so we can return a structured summary from sync calls."""


async def sync_full(
    *,
    user_id: str,
    days_back: int | None = 90,
    enrich: bool = True,
) -> GarminSyncReport:
    """Pull everything Garmin has on this user for the last `days_back` days.

    Args:
        days_back: How far back to look. 90 is the default for routine syncs;
            pass 365–730 for an all-time backfill on first connect, or pass
            None to auto-detect: we ask Garmin for the user's oldest activity
            and walk forward from there. Capped at 3650 days (~10 years) so
            a runaway probe can't hang the worker.
        enrich: When True (default), every activity gets a follow-up fetch for
            splits, HR/power zones, and weather — 4 API calls per activity.
            Set to False for fast historical backfills where summary-only data
            is enough; cuts a 700-activity import from ~60 min down to ~3 min.
            Daily metrics, performance snapshot, and PRs are always pulled.
    """
    tokens = load_tokens(user_id=user_id, provider="garmin")
    if not tokens:
        return GarminSyncReport(status="no_connection")

    provider = GarminProvider()

    # Auto-detect history start when days_back is None.
    if days_back is None:
        try:
            oldest = await provider.detect_history_start(tokens)
        except Exception as exc:  # noqa: BLE001
            log.warning("history auto-detect failed: %s — falling back to 730 days", exc)
            oldest = None
        if oldest:
            span = (datetime.now(timezone.utc) - oldest).days + 1
            days_back = min(max(span, 30), 3650)   # clamp 30d–10y
            log.info("history auto-detected: oldest activity %s → days_back=%d", oldest.date(), days_back)
        else:
            days_back = 730   # 2-year safety net

    since_dt = datetime.now(timezone.utc) - timedelta(days=days_back)
    since_date = since_dt.date()
    today = date.today()
    report = GarminSyncReport(
        status="ok", activities=0, splits=0, daily_metrics=0,
        performance_snapshots=0, personal_records=0, errors=[],
    )

    try:
        # 1) Activity list (summary fields only).
        activities = await provider.fetch_activities(tokens, since=since_dt)
        log.info("garmin sync: fetched %d activity summaries", len(activities))

        # 2) Optionally deep-enrich each activity (splits, HR zones, weather).
        #    Skip on big historical backfills — 4 API calls × ~700 activities
        #    is an hour of wall-clock time plus rate-limit risk. Routine
        #    syncs (last ~90 days) still enrich so the chart-ready data is
        #    fresh.
        if enrich:
            enriched = []
            for a in activities:
                try:
                    detail = await provider.fetch_activity_details(
                        tokens, source_id=a.source_id, base=a
                    )
                    enriched.append(detail or a)
                except (ProviderAuthError, ProviderRateLimitError):
                    raise
                except Exception as exc:  # noqa: BLE001
                    log.warning("activity %s detail fetch failed: %s", a.source_id, exc)
                    enriched.append(a)
                await asyncio.sleep(0.2)
        else:
            enriched = activities
            log.info("Skipping per-activity enrichment (enrich=False)")

        report["activities"] = upsert_activities(user_id=user_id, activities=enriched)
        report["splits"] = sum(len(a.splits) for a in enriched)

        # 3) Daily wellness across the window.
        metrics = await provider.fetch_daily_metrics(tokens, since=since_date, until=today)
        report["daily_metrics"] = upsert_daily_metrics(user_id=user_id, metrics=metrics)

        # 4) Performance snapshot — one row for today.
        perf = await provider.fetch_performance_snapshot(tokens, for_date=today)
        if perf and upsert_performance_snapshot(user_id=user_id, snapshot=perf):
            report["performance_snapshots"] = 1

        # 5) Personal records.
        prs = await provider.fetch_personal_records(tokens)
        report["personal_records"] = upsert_personal_records(user_id=user_id, records=prs)

        # 6) Profile sync — DOB, sex, weight, height from Garmin + max_hr
        #    derived from the highest observed workout max_hr in the last
        #    365 days. Runs BEFORE performance recompute so TRIMP/TSS use
        #    the right thresholds.
        try:
            athlete_profile = await provider.fetch_athlete_profile(tokens)
            profile_report = sync_profile_from_provider(
                user_id=user_id, provider_profile=athlete_profile
            )
            report["profile"] = profile_report
        except Exception as exc:  # noqa: BLE001
            log.warning("profile sync failed for %s: %s", user_id, exc)
            report["errors"].append(f"profile: {exc}")

        # 7) Recompute CTL/ATL/TSB/ACWR + per-workout TRIMP/TSS. Cheap (~1s).
        try:
            perf = recompute_for_user(user_id=user_id, lookback_days=180)
            report["performance_recomputed"] = perf.get("days_computed", 0)
        except Exception as exc:  # noqa: BLE001
            log.warning("performance recompute failed for %s: %s", user_id, exc)
            report["errors"].append(f"performance: {exc}")

        # 8) Compute derived metrics — VDOT, threshold, economy, fatigue
        #    resistance, recovery capacity. Pure DB-side math, no LLM.
        try:
            metrics = compute_all_metrics(user_id=user_id, lookback_days=180)
            report["metrics_computed"] = list(metrics.get("metrics", {}).keys())
        except Exception as exc:  # noqa: BLE001
            log.warning("metrics compute failed for %s: %s", user_id, exc)
            report["errors"].append(f"metrics: {exc}")

        # 9) Post-workout AI for any new key sessions in the last 48h.
        #    Costs ~1 LLM call per new key session; we skip silent days entirely.
        try:
            pw = analyze_recent_workouts(user_id=user_id, since_hours=48)
            report["post_workout_analyses"] = pw.get("analyzed", 0)
        except Exception as exc:  # noqa: BLE001
            log.warning("post-workout analysis failed for %s: %s", user_id, exc)
            report["errors"].append(f"post_workout: {exc}")

    except ProviderAuthError as exc:
        log.warning("garmin auth failed for user %s: %s", user_id, exc)
        mark_status(user_id=user_id, provider="garmin", status="expired")
        report["status"] = "auth_expired"
        report["errors"].append(str(exc))
    except ProviderRateLimitError as exc:
        log.warning("garmin rate-limited for user %s: %s", user_id, exc)
        report["status"] = "rate_limited"
        report["errors"].append(str(exc))
    except Exception as exc:  # noqa: BLE001
        log.exception("garmin sync_full crashed for user %s", user_id)
        report["status"] = "error"
        report["errors"].append(str(exc))

    return report


async def sync_incremental(*, user_id: str, default_window_days: int = 3) -> GarminSyncReport:
    """Lightweight daily sync — uses `oauth_connections.last_sync_at` as the
    cursor, with a small overlap to catch late-arriving data.
    """
    tokens = load_tokens(user_id=user_id, provider="garmin")
    if not tokens:
        return GarminSyncReport(status="no_connection")

    # last_sync_at lives on oauth_connections; for now we just use a fixed window.
    return await sync_full(user_id=user_id, days_back=default_window_days)

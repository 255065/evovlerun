"""Garmin Connect provider (unofficial — uses python-garminconnect).

ToS caveat: garminconnect talks to Garmin Connect's internal mobile API,
which is not officially exposed. Garmin can change endpoints or block at any
time, and a public production deployment is technically against their ToS.
Use this for personal / closed-beta integrations until the official Garmin
Wellness API partner program approves us; the provider abstraction makes
that swap a one-file change.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from app.services.providers.base import (
    CredentialLoginResult,
    NormalizedActivity,
    NormalizedDailyMetric,
    ProviderAuthError,
    ProviderClient,
    ProviderError,
    ProviderRateLimitError,
    ProviderTokens,
    Sport,
)
from app.services.providers.registry import register_provider

log = logging.getLogger(__name__)

_SPORT_MAP: dict[str, Sport] = {
    "running": "running",
    "treadmill_running": "running",
    "trail_running": "running",
    "track_running": "running",
    "indoor_running": "running",
    "virtual_run": "running",
    "cycling": "cycling",
    "road_biking": "cycling",
    "mountain_biking": "cycling",
    "gravel_cycling": "cycling",
    "indoor_cycling": "cycling",
    "virtual_ride": "cycling",
    "e_bike_fitness": "cycling",
    "swimming": "swimming",
    "lap_swimming": "swimming",
    "open_water_swimming": "swimming",
    "strength_training": "strength",
    "indoor_cardio": "strength",
    "walking": "walking",
    "hiking": "hiking",
}


def _run_blocking[T](func, *args, **kwargs) -> "asyncio.Future[T]":
    """Wrap a synchronous garminconnect call so it doesn't block the event loop."""
    return asyncio.get_running_loop().run_in_executor(None, lambda: func(*args, **kwargs))


def _normalize_garmin_sport(type_key: str | None) -> Sport:
    if not type_key:
        return "other"
    return _SPORT_MAP.get(type_key.lower(), "other")


def _to_iso_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    # Garmin returns e.g. "2026-05-16T10:30:00.0" — drop the trailing fractional zero
    # and assume UTC if no tz info.
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


class GarminProvider(ProviderClient):
    slug = "garmin"

    # -- Credential login --------------------------------------------------
    async def login_with_credentials(
        self, *, user_id: str, username: str, password: str
    ) -> CredentialLoginResult:
        """Initial login. Returns either tokens or a `needs_mfa` flag."""
        client = Garmin(email=username, password=password, return_on_mfa=True)
        try:
            mfa_status, _ = await _run_blocking(client.login)
        except GarminConnectAuthenticationError as exc:
            raise ProviderAuthError(str(exc)) from exc
        except GarminConnectTooManyRequestsError as exc:
            raise ProviderRateLimitError(str(exc)) from exc
        except GarminConnectConnectionError as exc:
            raise ProviderError(str(exc)) from exc

        if mfa_status == "needs_mfa":
            # Caller must store pending_state and call complete_credential_login
            # with the MFA code.
            pending_state = client.client.dumps()
            return CredentialLoginResult(needs_mfa=True, pending_state=pending_state)

        token_dump: str = client.client.dumps()
        return CredentialLoginResult(
            tokens=ProviderTokens(
                access_token=token_dump,
                refresh_token=None,
                expires_at=None,  # garminconnect refreshes silently
                provider_user_id=getattr(client, "display_name", None),
                extra={"display_name": getattr(client, "display_name", None)},
            )
        )

    async def complete_credential_login(
        self,
        *,
        user_id: str,
        pending_state: str,
        mfa_code: str,
        username: str,
        password: str,
    ) -> ProviderTokens:
        """Finish a 2FA-gated login by submitting the MFA code."""
        client = Garmin(email=username, password=password)

        def _resume():
            client.client.loads(pending_state)
            client.client.resume_login(client.client.__getstate__(), mfa_code)
            return client

        try:
            await _run_blocking(_resume)
        except GarminConnectAuthenticationError as exc:
            raise ProviderAuthError(str(exc)) from exc

        token_dump: str = client.client.dumps()
        return ProviderTokens(
            access_token=token_dump,
            refresh_token=None,
            expires_at=None,
            provider_user_id=getattr(client, "display_name", None),
            extra={"display_name": getattr(client, "display_name", None)},
        )

    async def refresh(self, tokens: ProviderTokens) -> ProviderTokens:
        # garminconnect refreshes internally on each call. If the session has
        # truly died, fetch_* will raise GarminConnectAuthenticationError and
        # the caller marks the connection expired.
        return tokens

    # -- Internal: restore client from tokens ------------------------------
    def _restore_client(self, tokens: ProviderTokens) -> Garmin:
        client = Garmin()
        try:
            # tokenstore >512 chars is treated as a serialized dump.
            client.login(tokenstore=tokens.access_token)
        except GarminConnectAuthenticationError as exc:
            raise ProviderAuthError(str(exc)) from exc
        except GarminConnectTooManyRequestsError as exc:
            raise ProviderRateLimitError(str(exc)) from exc
        except GarminConnectConnectionError as exc:
            raise ProviderError(str(exc)) from exc
        return client

    # -- Activities --------------------------------------------------------
    async def fetch_activities(
        self,
        tokens: ProviderTokens,
        *,
        since: datetime,
        until: datetime | None = None,
    ) -> list[NormalizedActivity]:
        client = await _run_blocking(self._restore_client, tokens)
        end = until or datetime.now(timezone.utc)
        start_date = since.date()
        end_date = end.date()

        try:
            raw_list = await _run_blocking(
                client.get_activities_by_date,
                start_date.isoformat(),
                end_date.isoformat(),
            )
        except GarminConnectAuthenticationError as exc:
            raise ProviderAuthError(str(exc)) from exc
        except GarminConnectTooManyRequestsError as exc:
            raise ProviderRateLimitError(str(exc)) from exc

        return [_normalize_activity(a) for a in (raw_list or [])]

    # -- Daily metrics -----------------------------------------------------
    async def fetch_daily_metrics(
        self,
        tokens: ProviderTokens,
        *,
        since: date,
        until: date | None = None,
    ) -> list[NormalizedDailyMetric]:
        """Pull sleep + HRV + body battery + readiness for each day in window."""
        client = await _run_blocking(self._restore_client, tokens)
        end = until or date.today()

        out: list[NormalizedDailyMetric] = []
        day = since
        while day <= end:
            try:
                sleep = await _run_blocking(client.get_sleep_data, day.isoformat())
                hrv = await _run_blocking(client.get_hrv_data, day.isoformat())
                # body battery / readiness can fail on older watches — best-effort.
                readiness = None
                try:
                    readiness = await _run_blocking(client.get_training_readiness, day.isoformat())
                except Exception:
                    readiness = None
            except GarminConnectAuthenticationError as exc:
                raise ProviderAuthError(str(exc)) from exc
            except GarminConnectTooManyRequestsError as exc:
                raise ProviderRateLimitError(str(exc)) from exc

            metric = _normalize_daily(day, sleep=sleep, hrv=hrv, readiness=readiness)
            if metric:
                out.append(metric)
            day += timedelta(days=1)

        return out


# ----------------------------------------------------------------------------
# Normalizers
# ----------------------------------------------------------------------------
def _normalize_activity(raw: dict[str, Any]) -> NormalizedActivity:
    sport = _normalize_garmin_sport(
        (raw.get("activityType") or {}).get("typeKey") if isinstance(raw.get("activityType"), dict) else None
    )
    started = _to_iso_datetime(raw.get("startTimeGMT") or raw.get("startTimeLocal"))
    if started is None:
        started = datetime.now(timezone.utc)

    avg_speed = raw.get("averageSpeed")  # m/s
    pace_s_per_km: float | None = None
    if sport in ("running", "walking", "hiking") and avg_speed and avg_speed > 0:
        pace_s_per_km = round(1000.0 / avg_speed, 2)

    return NormalizedActivity(
        source="garmin",
        source_id=str(raw.get("activityId")),
        sport=sport,
        started_at=started,
        duration_seconds=int(raw.get("duration") or raw.get("movingDuration") or 0),
        distance_m=float(raw["distance"]) if raw.get("distance") is not None else None,
        elevation_gain_m=raw.get("elevationGain"),
        avg_hr=int(raw["averageHR"]) if raw.get("averageHR") else None,
        max_hr=int(raw["maxHR"]) if raw.get("maxHR") else None,
        avg_pace_s_per_km=pace_s_per_km,
        avg_power_w=raw.get("avgPower"),
        normalized_power_w=raw.get("normPower"),
        trimp=raw.get("aerobicTrainingEffect"),  # Garmin's TE 0-5 scale — not strictly TRIMP
        tss=None,
        perceived_effort=raw.get("workoutFeel"),
        notes=raw.get("activityName"),
        raw_payload=raw,
    )


def _normalize_daily(
    day: date,
    *,
    sleep: dict[str, Any] | None,
    hrv: dict[str, Any] | None,
    readiness: list | dict | None,
) -> NormalizedDailyMetric | None:
    sleep_dto = (sleep or {}).get("dailySleepDTO") or {}
    sleep_total_seconds = sleep_dto.get("sleepTimeSeconds")
    sleep_score = ((sleep_dto.get("sleepScores") or {}).get("overall") or {}).get("value")

    hrv_summary = (hrv or {}).get("hrvSummary") or {}
    last_night_avg = hrv_summary.get("lastNightAvg")

    readiness_obj = readiness[0] if isinstance(readiness, list) and readiness else readiness
    readiness_score = (readiness_obj or {}).get("score") if isinstance(readiness_obj, dict) else None
    body_battery = (readiness_obj or {}).get("bodyBatteryLevel") if isinstance(readiness_obj, dict) else None

    # Skip rows that contain nothing useful so we don't write empty days.
    if not any([sleep_total_seconds, last_night_avg, readiness_score, body_battery]):
        return None

    return NormalizedDailyMetric(
        metric_date=day,
        resting_hr=sleep_dto.get("restingHeartRate"),
        hrv_rmssd=float(last_night_avg) if last_night_avg is not None else None,
        sleep_minutes=int(sleep_total_seconds / 60) if sleep_total_seconds else None,
        sleep_score=int(sleep_score) if sleep_score is not None else None,
        readiness_score=int(readiness_score) if readiness_score is not None else None,
        body_battery=int(body_battery) if body_battery is not None else None,
        weight_kg=None,
        body_temp_delta=None,
        raw_payload={"sleep": sleep, "hrv": hrv, "readiness": readiness},
    )


register_provider(GarminProvider.slug, GarminProvider)

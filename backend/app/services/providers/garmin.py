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
    NormalizedAthleteProfile,
    NormalizedDailyMetric,
    NormalizedPerformanceSnapshot,
    NormalizedPersonalRecord,
    NormalizedSplit,
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


async def _safe_call(func, *args, **kwargs):
    """Run a blocking Garmin endpoint and swallow non-auth errors.

    Many Garmin endpoints 404 on older devices or return malformed JSON on
    days when the watch wasn't worn. We catch those so a single missing field
    doesn't kill the whole sync, but we propagate auth and rate-limit errors
    so the caller can react.
    """
    try:
        return await _run_blocking(func, *args, **kwargs)
    except (GarminConnectAuthenticationError, GarminConnectTooManyRequestsError):
        raise
    except Exception as exc:  # noqa: BLE001 — best-effort per endpoint
        log.debug("Garmin endpoint %s failed: %s", getattr(func, "__name__", "?"), exc)
        return None


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
        """Pull the full daily wellness bundle for each day in window.

        Each fetch is best-effort — Garmin returns 200/empty for days the watch
        wasn't worn, and individual endpoints can 404 on older devices (body
        battery, SpO2, respiration). We swallow per-endpoint errors and only
        raise on auth/rate-limit so the sync can still write everything else.
        """
        client = await _run_blocking(self._restore_client, tokens)
        end = until or date.today()

        out: list[NormalizedDailyMetric] = []
        day = since
        while day <= end:
            iso = day.isoformat()
            try:
                # Core (always try — these are the most reliable).
                sleep = await _safe_call(client.get_sleep_data, iso)
                hrv = await _safe_call(client.get_hrv_data, iso)
                readiness = await _safe_call(client.get_training_readiness, iso)
                # Optional richer fields — older watches may not have them.
                stress = await _safe_call(client.get_stress_data, iso)
                spo2 = await _safe_call(client.get_spo2_data, iso)
                respiration = await _safe_call(client.get_respiration_data, iso)
                steps = await _safe_call(client.get_steps_data, iso)
                user_summary = await _safe_call(client.get_user_summary, iso)
                intensity = await _safe_call(client.get_intensity_minutes_data, iso)
                body_comp = await _safe_call(client.get_body_composition, iso)
                floors = await _safe_call(client.get_floors, iso)
            except GarminConnectAuthenticationError as exc:
                raise ProviderAuthError(str(exc)) from exc
            except GarminConnectTooManyRequestsError as exc:
                raise ProviderRateLimitError(str(exc)) from exc

            metric = _normalize_daily(
                day,
                sleep=sleep,
                hrv=hrv,
                readiness=readiness,
                stress=stress,
                spo2=spo2,
                respiration=respiration,
                steps=steps,
                user_summary=user_summary,
                intensity=intensity,
                body_comp=body_comp,
                floors=floors,
            )
            if metric:
                out.append(metric)
            day += timedelta(days=1)

        return out

    # -- Single activity deep-dive ----------------------------------------
    async def fetch_activity_details(
        self,
        tokens: ProviderTokens,
        *,
        source_id: str,
        base: NormalizedActivity | None = None,
    ) -> NormalizedActivity | None:
        """Hydrate one Garmin activity with splits, HR/power zones, weather.

        If `base` is provided, we enrich it in place — preferred path because
        `get_activity(id)` returns data nested under `summaryDTO`/`activityTypeDTO`
        which is brittle to re-normalize. Without `base` we fall back to
        normalizing the summary blob.
        """
        client = await _run_blocking(self._restore_client, tokens)
        try:
            splits_raw = await _safe_call(client.get_activity_splits, source_id) \
                or await _safe_call(client.get_activity_typed_splits, source_id)
            hr_tz = await _safe_call(client.get_activity_hr_in_timezones, source_id)
            power_tz = await _safe_call(client.get_activity_power_in_timezones, source_id)
            weather = await _safe_call(client.get_activity_weather, source_id)
            # Only fetch the full activity blob when we need it as a fallback.
            raw = None if base else await _safe_call(client.get_activity, source_id)
        except GarminConnectAuthenticationError as exc:
            raise ProviderAuthError(str(exc)) from exc
        except GarminConnectTooManyRequestsError as exc:
            raise ProviderRateLimitError(str(exc)) from exc

        if base is None and raw is None:
            return None

        activity = base if base is not None else _normalize_activity(_flatten_garmin_blob(raw))
        activity.hr_zone_seconds = _zones_to_dict(hr_tz)
        activity.power_zone_seconds = _zones_to_dict(power_tz)
        activity.weather_payload = weather if isinstance(weather, dict) else None
        activity.temperature_c = _extract_temp(weather)
        activity.splits = _normalize_splits(splits_raw)
        activity.cardiac_drift_pct = _cardiac_drift(activity.splits)
        activity.pace_decay_pct = _pace_decay(activity.splits, sport=activity.sport)
        activity.polarized_score = _polarized_score(activity.hr_zone_seconds)
        return activity

    # -- Performance snapshot ---------------------------------------------
    async def fetch_performance_snapshot(
        self,
        tokens: ProviderTokens,
        *,
        for_date: date | None = None,
    ) -> NormalizedPerformanceSnapshot | None:
        """Garmin's own performance estimates for the given date (default today)."""
        client = await _run_blocking(self._restore_client, tokens)
        day = for_date or date.today()
        iso = day.isoformat()

        try:
            max_metrics = await _safe_call(client.get_max_metrics, iso)
            lt = await _safe_call(client.get_lactate_threshold, iso)
            race_pred = await _safe_call(client.get_race_predictions)
            training_status = await _safe_call(client.get_training_status, iso)
            endurance = await _safe_call(client.get_endurance_score, iso)
            hill = await _safe_call(client.get_hill_score, iso)
            fitness_age = await _safe_call(client.get_fitnessage_data, iso)
            running_tol = await _safe_call(client.get_running_tolerance, iso)
            body_comp = await _safe_call(client.get_body_composition, iso)
            ftp = await _safe_call(client.get_cycling_ftp)
        except GarminConnectAuthenticationError as exc:
            raise ProviderAuthError(str(exc)) from exc
        except GarminConnectTooManyRequestsError as exc:
            raise ProviderRateLimitError(str(exc)) from exc

        snap = _normalize_performance(
            day,
            max_metrics=max_metrics,
            lt=lt,
            race_pred=race_pred,
            training_status=training_status,
            endurance=endurance,
            hill=hill,
            fitness_age=fitness_age,
            running_tol=running_tol,
            body_comp=body_comp,
            ftp=ftp,
        )
        return snap

    # -- Personal records --------------------------------------------------
    async def fetch_personal_records(
        self,
        tokens: ProviderTokens,
    ) -> list[NormalizedPersonalRecord]:
        client = await _run_blocking(self._restore_client, tokens)
        try:
            prs = await _safe_call(client.get_personal_record)
        except GarminConnectAuthenticationError as exc:
            raise ProviderAuthError(str(exc)) from exc

        return _normalize_personal_records(prs or [])

    # -- Athlete profile ---------------------------------------------------
    async def fetch_athlete_profile(
        self,
        tokens: ProviderTokens,
    ) -> NormalizedAthleteProfile | None:
        """Pull DOB, sex, weight, height, VO2max from Garmin's user profile.

        Garmin does NOT expose `userMaxHr` reliably — instead we derive max HR
        upstream from the highest observed `max_hr` across the user's workouts.
        Resting HR is taken from the most recent daily_metrics row.
        """
        client = await _run_blocking(self._restore_client, tokens)
        try:
            profile = await _safe_call(client.get_user_profile)
        except GarminConnectAuthenticationError as exc:
            raise ProviderAuthError(str(exc)) from exc

        return _normalize_athlete_profile(profile)


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
        trimp=None,  # Garmin doesn't expose TRIMP directly — we compute later
        tss=None,
        perceived_effort=raw.get("workoutFeel"),
        notes=raw.get("activityName"),
        # Deep fields straight from the summary blob.
        cadence_avg=int(raw["averageRunningCadenceInStepsPerMinute"])
            if raw.get("averageRunningCadenceInStepsPerMinute") else
            (int(raw["averageBikingCadenceInRevPerMinute"])
             if raw.get("averageBikingCadenceInRevPerMinute") else None),
        cadence_max=int(raw["maxRunningCadenceInStepsPerMinute"])
            if raw.get("maxRunningCadenceInStepsPerMinute") else None,
        calories=int(raw["calories"]) if raw.get("calories") else None,
        aerobic_te=raw.get("aerobicTrainingEffect"),
        anaerobic_te=raw.get("anaerobicTrainingEffect"),
        training_load=raw.get("activityTrainingLoad"),
        vo2max_at_activity=raw.get("vO2MaxValue"),
        raw_payload=raw,
    )


def _normalize_daily(
    day: date,
    *,
    sleep: dict[str, Any] | None,
    hrv: dict[str, Any] | None,
    readiness: list | dict | None,
    stress: dict[str, Any] | None = None,
    spo2: dict[str, Any] | None = None,
    respiration: dict[str, Any] | None = None,
    steps: list | dict | None = None,
    user_summary: dict[str, Any] | None = None,
    intensity: dict[str, Any] | None = None,
    body_comp: dict[str, Any] | None = None,
    floors: dict[str, Any] | None = None,
) -> NormalizedDailyMetric | None:
    sleep_dto = (sleep or {}).get("dailySleepDTO") or {}
    sleep_total_seconds = sleep_dto.get("sleepTimeSeconds")
    sleep_score = ((sleep_dto.get("sleepScores") or {}).get("overall") or {}).get("value")

    hrv_summary = (hrv or {}).get("hrvSummary") or {}
    last_night_avg = hrv_summary.get("lastNightAvg")

    readiness_obj = readiness[0] if isinstance(readiness, list) and readiness else readiness
    readiness_score = (readiness_obj or {}).get("score") if isinstance(readiness_obj, dict) else None
    body_battery = (readiness_obj or {}).get("bodyBatteryLevel") if isinstance(readiness_obj, dict) else None

    # User summary has stress + intensity minutes + floors aggregated.
    summary = user_summary if isinstance(user_summary, dict) else {}
    stress_avg = (stress or {}).get("avgStressLevel") if isinstance(stress, dict) else summary.get("averageStressLevel")
    stress_max = (stress or {}).get("maxStressLevel") if isinstance(stress, dict) else summary.get("maxStressLevel")

    spo2_avg = (spo2 or {}).get("averageSpO2") if isinstance(spo2, dict) else None
    spo2_min = (spo2 or {}).get("lowestSpO2") if isinstance(spo2, dict) else None

    resp = respiration if isinstance(respiration, dict) else {}
    respiration_avg = resp.get("avgWakingRespirationValue") or resp.get("avgRespirationValue")
    respiration_min = resp.get("lowestRespirationValue")
    respiration_max = resp.get("highestRespirationValue")

    # Steps: get_steps_data can return a list of granular buckets; get_user_summary aggregates.
    steps_total = summary.get("totalSteps")
    if not steps_total and isinstance(steps, list):
        steps_total = sum((s.get("steps") or 0) for s in steps if isinstance(s, dict)) or None

    floors_climbed = summary.get("floorsAscended") or (floors or {}).get("floorsAscended") if isinstance(floors, dict) else summary.get("floorsAscended")
    im_moderate = summary.get("moderateIntensityMinutes")
    im_vigorous = summary.get("vigorousIntensityMinutes")
    if isinstance(intensity, dict):
        im_moderate = im_moderate or intensity.get("moderateIntensityMinutes")
        im_vigorous = im_vigorous or intensity.get("vigorousIntensityMinutes")

    active_cal = summary.get("activeKilocalories")
    total_cal = summary.get("totalKilocalories")

    # Body composition (latest weigh-in for the day).
    weight_kg = None
    body_fat = None
    if isinstance(body_comp, dict):
        date_weights = body_comp.get("dateWeightList") or []
        if date_weights:
            latest = date_weights[-1]
            if latest.get("weight"):
                weight_kg = round(float(latest["weight"]) / 1000.0, 2)  # grams → kg
            body_fat = latest.get("bodyFat")

    # Resting HR fallbacks: sleep DTO > user summary > readiness.
    resting_hr = (
        sleep_dto.get("restingHeartRate")
        or summary.get("restingHeartRate")
        or (readiness_obj or {}).get("restingHeartRate") if isinstance(readiness_obj, dict) else None
    )

    # Skip rows that contain nothing useful.
    if not any([
        sleep_total_seconds, last_night_avg, readiness_score, body_battery,
        stress_avg, steps_total, spo2_avg, respiration_avg, weight_kg,
    ]):
        return None

    return NormalizedDailyMetric(
        metric_date=day,
        resting_hr=int(resting_hr) if resting_hr else None,
        hrv_rmssd=float(last_night_avg) if last_night_avg is not None else None,
        sleep_minutes=int(sleep_total_seconds / 60) if sleep_total_seconds else None,
        sleep_score=int(sleep_score) if sleep_score is not None else None,
        readiness_score=int(readiness_score) if readiness_score is not None else None,
        body_battery=int(body_battery) if body_battery is not None else None,
        weight_kg=weight_kg,
        body_temp_delta=None,
        stress_avg=int(stress_avg) if stress_avg not in (None, -1) else None,
        stress_max=int(stress_max) if stress_max not in (None, -1) else None,
        steps=int(steps_total) if steps_total else None,
        floors_climbed=int(floors_climbed) if floors_climbed else None,
        intensity_minutes_moderate=int(im_moderate) if im_moderate else None,
        intensity_minutes_vigorous=int(im_vigorous) if im_vigorous else None,
        spo2_avg=int(spo2_avg) if spo2_avg else None,
        spo2_min=int(spo2_min) if spo2_min else None,
        respiration_avg=int(respiration_avg) if respiration_avg else None,
        respiration_min=int(respiration_min) if respiration_min else None,
        respiration_max=int(respiration_max) if respiration_max else None,
        body_fat_pct=float(body_fat) if body_fat else None,
        active_calories=int(active_cal) if active_cal else None,
        total_calories=int(total_cal) if total_cal else None,
        raw_payload={
            "sleep": sleep, "hrv": hrv, "readiness": readiness,
            "stress": stress, "spo2": spo2, "respiration": respiration,
            "user_summary": user_summary, "body_comp": body_comp,
        },
    )


def _flatten_garmin_blob(raw: dict[str, Any] | None) -> dict[str, Any]:
    """Garmin's `get_activity(id)` returns a nested blob:
       {activityId, activityName, summaryDTO: {...all fields...}, activityTypeDTO: {...}}
    while `get_activities_by_date` flattens those into the top level. We
    promote the nested fields so a single normalizer handles both shapes.
    """
    if not raw:
        return {}
    out = dict(raw)
    summary = raw.get("summaryDTO") or {}
    type_dto = raw.get("activityTypeDTO") or {}
    # summaryDTO carries the bulk of the metrics.
    for k, v in summary.items():
        out.setdefault(k, v)
    # activityTypeDTO mirrors the activityType key from the list endpoint.
    if type_dto and not out.get("activityType"):
        out["activityType"] = type_dto
    return out


def _normalize_splits(raw: Any) -> list[NormalizedSplit]:
    """Garmin splits come in two shapes:
      get_activity_splits → {lapDTOs: [...]}
      get_activity_typed_splits → {splits: [...]}
    Both contain the same per-lap fields with slightly different naming.
    """
    if not raw:
        return []
    if isinstance(raw, dict):
        lap_list = raw.get("lapDTOs") or raw.get("splits")
    else:
        lap_list = raw
    if not isinstance(lap_list, list):
        return []

    out: list[NormalizedSplit] = []
    for i, lap in enumerate(lap_list, start=1):
        if not isinstance(lap, dict):
            continue
        speed = lap.get("averageSpeed")
        pace_s = round(1000.0 / speed, 2) if speed and speed > 0 else None
        out.append(NormalizedSplit(
            split_index=i,
            split_type=lap.get("intensityType") or lap.get("lapType") or "lap",
            duration_s=int(lap["duration"]) if lap.get("duration") else None,
            distance_m=float(lap["distance"]) if lap.get("distance") else None,
            avg_hr=int(lap["averageHR"]) if lap.get("averageHR") else None,
            max_hr=int(lap["maxHR"]) if lap.get("maxHR") else None,
            avg_pace_s_per_km=pace_s,
            avg_speed_mps=speed,
            avg_cadence=int(lap["averageRunCadence"]) if lap.get("averageRunCadence") else None,
            avg_power_w=lap.get("averagePower"),
            elevation_gain_m=lap.get("elevationGain"),
            intensity=lap.get("intensityType"),
        ))
    return out


def _zones_to_dict(raw: Any) -> dict[str, int] | None:
    """Convert Garmin's HR/power zone array to {z1, z2, ..., z5} seconds."""
    if not isinstance(raw, list) or not raw:
        return None
    out: dict[str, int] = {}
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        zone = entry.get("zoneNumber") or entry.get("zone")
        secs = entry.get("secsInZone") or entry.get("seconds")
        if zone is not None and secs is not None:
            out[f"z{int(zone)}"] = int(secs)
    return out or None


def _extract_temp(weather: Any) -> float | None:
    if not isinstance(weather, dict):
        return None
    return weather.get("temp") or weather.get("apparentTemp")


def _cardiac_drift(splits: list[NormalizedSplit]) -> float | None:
    """% drift in avg HR between first-half and second-half splits.

    Useful proxy for aerobic decoupling — see Friel's HR/pace drift method.
    Returns None when we don't have enough laps with HR.
    """
    laps = [s for s in splits if s.avg_hr and s.duration_s]
    if len(laps) < 4:
        return None
    mid = len(laps) // 2
    first_avg = sum(s.avg_hr for s in laps[:mid]) / mid
    second_avg = sum(s.avg_hr for s in laps[mid:]) / (len(laps) - mid)
    if first_avg == 0:
        return None
    return round((second_avg - first_avg) / first_avg * 100, 2)


def _pace_decay(splits: list[NormalizedSplit], *, sport: Sport) -> float | None:
    """% pace slowdown from first-half to second-half (running/walking/hiking only).

    Positive = slower second half (decay). Negative = neg-split.
    """
    if sport not in ("running", "walking", "hiking"):
        return None
    laps = [s for s in splits if s.avg_pace_s_per_km and s.duration_s]
    if len(laps) < 4:
        return None
    mid = len(laps) // 2
    first_pace = sum(s.avg_pace_s_per_km for s in laps[:mid]) / mid
    second_pace = sum(s.avg_pace_s_per_km for s in laps[mid:]) / (len(laps) - mid)
    if first_pace == 0:
        return None
    return round((second_pace - first_pace) / first_pace * 100, 2)


def _polarized_score(hr_zones: dict[str, int] | None) -> float | None:
    """Ratio of (z1+z2) low-intensity to (z4+z5) high-intensity time.

    A common heuristic: >80% in z1-2 + 10–20% in z4-5 = polarized.
    We return the % of total time spent in z1+z2 (the "easy" share).
    """
    if not hr_zones:
        return None
    total = sum(hr_zones.values())
    if total == 0:
        return None
    easy = (hr_zones.get("z1", 0) + hr_zones.get("z2", 0))
    return min(99.99, round(easy / total * 100, 2))


def _normalize_performance(
    day: date,
    *,
    max_metrics: Any,
    lt: Any,
    race_pred: Any,
    training_status: Any,
    endurance: Any,
    hill: Any,
    fitness_age: Any,
    running_tol: Any,
    body_comp: Any,
    ftp: Any,
) -> NormalizedPerformanceSnapshot:
    """Map Garmin's heterogeneous performance endpoints into one row."""
    # VO2max: get_max_metrics returns a list with a `generic` (running) and `cycling` block.
    vo2_running: float | None = None
    if isinstance(max_metrics, list) and max_metrics:
        first = max_metrics[0]
        if isinstance(first, dict):
            generic = first.get("generic") or {}
            vo2_running = generic.get("vo2MaxValue") or generic.get("vo2MaxPreciseValue")

    # Lactate threshold.
    lt_hr: int | None = None
    lt_pace_s: float | None = None
    if isinstance(lt, dict):
        lt_hr = lt.get("lactateThresholdHeartRate") or lt.get("calendarDate") and lt.get("lactateThresholdHR")
        lt_pace_speed = lt.get("lactateThresholdSpeed")
        if lt_pace_speed:
            lt_pace_s = round(1000.0 / lt_pace_speed, 2)

    # Race predictions.
    rp = race_pred[0] if isinstance(race_pred, list) and race_pred else race_pred if isinstance(race_pred, dict) else {}
    rp = rp or {}

    # Training status.
    ts_obj = training_status if isinstance(training_status, dict) else {}
    ts_text: str | None = None
    most_recent = ts_obj.get("mostRecentTrainingStatus") or {}
    if isinstance(most_recent, dict):
        latest = (most_recent.get("latestTrainingStatusData") or {})
        if latest:
            # The "latest" dict is keyed by device id; take any value.
            for v in latest.values():
                if isinstance(v, dict) and v.get("trainingStatusFeedbackPhrase"):
                    ts_text = v.get("trainingStatusFeedbackPhrase") or v.get("trainingStatus")
                    break

    # Endurance / hill / fitness age / running tolerance.
    endurance_score = (endurance or {}).get("overallScore") if isinstance(endurance, dict) else None
    hill_score = (hill or {}).get("overallScore") if isinstance(hill, dict) else None
    fitness_age_val = (fitness_age or {}).get("chronologicalAge") if isinstance(fitness_age, dict) else None
    # Actually fitnessAge is the value we want, not chronological age:
    if isinstance(fitness_age, dict):
        fitness_age_val = fitness_age.get("fitnessAge") or fitness_age_val
    running_tol_val = (running_tol or {}).get("runningTolerance") if isinstance(running_tol, dict) else None

    # Body composition (latest entry of the day).
    body_fat: float | None = None
    muscle: float | None = None
    if isinstance(body_comp, dict):
        date_weights = body_comp.get("dateWeightList") or []
        if date_weights:
            latest = date_weights[-1]
            body_fat = latest.get("bodyFat")
            if latest.get("muscleMass"):
                muscle = round(float(latest["muscleMass"]) / 1000.0, 2)

    # FTP (cycling): get_cycling_ftp returns either a number or dict {ftp: N}.
    ftp_w: float | None = None
    if isinstance(ftp, dict):
        ftp_w = ftp.get("ftp") or ftp.get("functionalThresholdPower")
    elif isinstance(ftp, (int, float)):
        ftp_w = float(ftp)

    return NormalizedPerformanceSnapshot(
        snapshot_date=day,
        garmin_training_status=ts_text,
        garmin_training_load_focus=ts_obj.get("trainingLoadFocus") if isinstance(ts_obj, dict) else None,
        garmin_endurance_score=int(endurance_score) if endurance_score else None,
        garmin_hill_score=int(hill_score) if hill_score else None,
        garmin_fitness_age=int(fitness_age_val) if fitness_age_val else None,
        garmin_running_tolerance=int(running_tol_val) if running_tol_val else None,
        garmin_vo2max=float(vo2_running) if vo2_running else None,
        garmin_lt_hr=int(lt_hr) if lt_hr else None,
        garmin_lt_pace_s_per_km=lt_pace_s,
        race_prediction_5k_s=int(rp.get("time5K")) if rp.get("time5K") else None,
        race_prediction_10k_s=int(rp.get("time10K")) if rp.get("time10K") else None,
        race_prediction_hm_s=int(rp.get("timeHalfMarathon")) if rp.get("timeHalfMarathon") else None,
        race_prediction_marathon_s=int(rp.get("timeMarathon")) if rp.get("timeMarathon") else None,
        body_fat_pct=float(body_fat) if body_fat else None,
        muscle_mass_kg=muscle,
        ftp_w=ftp_w,
        raw_payload={
            "max_metrics": max_metrics, "lt": lt, "race_pred": race_pred,
            "training_status": training_status, "endurance": endurance,
            "hill": hill, "fitness_age": fitness_age, "running_tol": running_tol,
            "body_comp": body_comp, "ftp": ftp,
        },
    )


def _normalize_athlete_profile(raw: Any) -> NormalizedAthleteProfile | None:
    """Map Garmin's user_profile blob to our profile shape.

    Garmin's weight is in grams, height in cm. Sex comes as MALE/FEMALE/OTHER.
    `userMaxHr` is almost always None — we leave max_hr out here and let the
    sync layer fill it from observed workout max_hr (more reliable anyway).
    """
    if not isinstance(raw, dict):
        return None
    ud = raw.get("userData") or {}
    if not ud:
        return None

    sex_map = {"MALE": "male", "FEMALE": "female", "OTHER": "other"}
    sex = sex_map.get((ud.get("gender") or "").upper())

    weight_g = ud.get("weight")
    weight_kg = round(float(weight_g) / 1000.0, 2) if weight_g else None
    height_cm = float(ud.get("height")) if ud.get("height") else None

    dob: date | None = None
    if ud.get("birthDate"):
        try:
            dob = date.fromisoformat(ud["birthDate"])
        except ValueError:
            dob = None

    lt_hr = ud.get("lactateThresholdHeartRate") or None
    if isinstance(lt_hr, (int, float)) and lt_hr <= 0:
        lt_hr = None

    return NormalizedAthleteProfile(
        date_of_birth=dob,
        sex=sex,
        weight_kg=weight_kg,
        height_cm=height_cm,
        max_hr=ud.get("userMaxHr"),
        resting_hr=None,
        lactate_threshold_hr=int(lt_hr) if lt_hr else None,
        vo2max_running=float(ud["vo2MaxRunning"]) if ud.get("vo2MaxRunning") else None,
        raw_payload=raw,
    )


def _normalize_personal_records(raw: list[dict[str, Any]]) -> list[NormalizedPersonalRecord]:
    """Garmin PRs come as a list of {typeId, value, prStartTimeGmt, activityId}.

    typeId mapping (running, approximate — Garmin doesn't publish this):
      1 = 1k, 2 = 1mi, 3 = 5k, 4 = 10k, 5 = HM, 6 = marathon,
      7 = longest run, 8 = longest ride, 9 = biggest climb (m), 10 = longest swim,
      12 = best cycling power 5s, 13 = 60s, 14 = 5min, 15 = 20min FTP estimate
    """
    type_map = {
        1: ("best_1k_s", "s"), 2: ("best_1mi_s", "s"), 3: ("best_5k_s", "s"),
        4: ("best_10k_s", "s"), 5: ("best_hm_s", "s"), 6: ("best_marathon_s", "s"),
        7: ("longest_run_m", "m"), 8: ("longest_ride_m", "m"),
        9: ("biggest_climb_m", "m"), 10: ("longest_swim_m", "m"),
        12: ("best_power_5s_w", "w"), 13: ("best_power_60s_w", "w"),
        14: ("best_power_5min_w", "w"), 15: ("ftp_estimate_w", "w"),
    }
    out: list[NormalizedPersonalRecord] = []
    for rec in raw or []:
        if not isinstance(rec, dict):
            continue
        type_id = rec.get("typeId")
        info = type_map.get(int(type_id)) if type_id is not None else None
        if not info:
            continue
        rec_type, unit = info
        val = rec.get("value")
        if val is None:
            continue
        achieved_at = _to_iso_datetime(rec.get("prStartTimeGmtFormatted") or rec.get("prStartTimeGmt"))
        out.append(NormalizedPersonalRecord(
            source="garmin",
            record_type=rec_type,
            value=float(val),
            unit=unit,
            achieved_at=achieved_at,
            activity_source_id=str(rec.get("activityId")) if rec.get("activityId") else None,
            raw_payload=rec,
        ))
    return out


register_provider(GarminProvider.slug, GarminProvider)

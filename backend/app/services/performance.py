"""Performance model — Banister TRIMP, hrTSS, CTL/ATL/TSB, ACWR.

The math:

  TRIMP (Banister 1991)
    HR_ratio = (HR_avg - HR_rest) / (HR_max - HR_rest)
    y = 0.64 * exp(1.92 * HR_ratio)   for males
    y = 0.86 * exp(1.67 * HR_ratio)   for females
    TRIMP = duration_min * HR_ratio * y

  hrTSS (heart-rate based TSS — Coggan adapted for HR)
    IF = HR_avg / lactate_threshold_HR
    TSS = duration_min * IF^2 * (100/60)   ≈ TSS per hour of work at LT

  CTL / ATL (exponentially-weighted moving averages of daily TSS)
    α_ctl = 1 - exp(-1/42)   ≈ 0.0235
    α_atl = 1 - exp(-1/7)    ≈ 0.1331
    CTL[d] = CTL[d-1] + α_ctl * (TSS[d] - CTL[d-1])
    ATL[d] = ATL[d-1] + α_atl * (TSS[d] - ATL[d-1])

  TSB = CTL - ATL                          (positive = fresh, negative = fatigued)
  ACWR = ATL_load_7d / (CTL_load_28d / 4)  (Gabbett's rolling ratio variant)

  ACWR zones:
    < 0.8     detraining / undertrained
    0.8–1.3   optimal sweet spot
    1.3–1.5   elevated injury risk
    > 1.5     high injury risk ("danger zone")

We compute one row per day in `performance_profiles`, even on rest days — the
EMAs need continuous time series. Garmin's own snapshot fields (VO2max, LT,
race predictions) stay untouched when we recompute load metrics.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.supabase import get_supabase_admin

log = logging.getLogger(__name__)

# Exponential smoothing factors — see module docstring.
ALPHA_CTL = 1 - math.exp(-1 / 42)
ALPHA_ATL = 1 - math.exp(-1 / 7)

# Reasonable defaults when the user's profile is incomplete.
DEFAULT_RESTING_HR = 50
DEFAULT_MAX_HR_FALLBACK = 190   # used only if profile + Garmin both blank
DEFAULT_LT_HR_FRACTION = 0.88   # LT ≈ 88% of HRmax as a fallback


# ---------------------------------------------------------------------------
# Per-workout intensity scores
# ---------------------------------------------------------------------------
def compute_trimp(
    *,
    duration_seconds: int,
    avg_hr: int | None,
    max_hr: int,
    resting_hr: int,
    sex: str | None = "male",
) -> float | None:
    """Banister TRIMP. Returns None if HR data is missing.

    Note: Banister's coefficients were fit to male data; the female variant
    (0.86 * exp(1.67x)) is from a 1992 follow-up and slightly underweights
    high intensity vs. males. Use whichever matches the athlete's sex.
    """
    if not avg_hr or not duration_seconds:
        return None
    if max_hr <= resting_hr:
        return None
    hr_ratio = (avg_hr - resting_hr) / (max_hr - resting_hr)
    hr_ratio = max(0.0, min(hr_ratio, 1.0))
    duration_min = duration_seconds / 60.0
    if sex == "female":
        y = 0.86 * math.exp(1.67 * hr_ratio)
    else:
        y = 0.64 * math.exp(1.92 * hr_ratio)
    return round(duration_min * hr_ratio * y, 2)


def compute_hr_tss(
    *,
    duration_seconds: int,
    avg_hr: int | None,
    lt_hr: int | None,
) -> float | None:
    """Heart-rate-based TSS.

    A 1-hour effort at LT-HR equals exactly 100 TSS, mirroring Coggan's
    power-based definition. Returns None when we lack LT-HR.
    """
    if not avg_hr or not lt_hr or not duration_seconds:
        return None
    if lt_hr <= 0:
        return None
    intensity = avg_hr / lt_hr
    duration_min = duration_seconds / 60.0
    return round(duration_min * (intensity ** 2) * (100.0 / 60.0), 2)


# ---------------------------------------------------------------------------
# Daily aggregation + EMA recompute
# ---------------------------------------------------------------------------
@dataclass
class DailyLoad:
    day: date
    tss: float
    trimp: float


@dataclass
class PerformancePoint:
    day: date
    tss: float
    trimp: float
    ctl: float
    atl: float
    tsb: float
    acwr: float | None
    acwr_zone: str | None


def _classify_acwr(acwr: float | None) -> str | None:
    if acwr is None:
        return None
    if acwr < 0.8:
        return "detraining_or_undertrained"
    if acwr <= 1.3:
        return "optimal"
    if acwr <= 1.5:
        return "elevated_risk"
    return "high_injury_risk"


def _resolve_thresholds(profile: dict, latest_perf: dict | None) -> dict[str, int | str]:
    """Pick the best available HR thresholds for this user.

    Priority for LT HR:  Garmin LT > our estimated LT > 0.88 * max_hr.
    Priority for max HR: profile.max_hr > 220 - age fallback > 190.
    """
    max_hr: int | None = profile.get("max_hr")
    # 220 - age estimate if profile didn't set it.
    if not max_hr and profile.get("date_of_birth"):
        try:
            dob = datetime.fromisoformat(profile["date_of_birth"]).date()
            age = (date.today() - dob).days // 365
            max_hr = 220 - age
        except (ValueError, TypeError):
            pass
    if not max_hr:
        max_hr = DEFAULT_MAX_HR_FALLBACK

    resting_hr = profile.get("resting_hr") or DEFAULT_RESTING_HR

    lt_hr: int | None = None
    if latest_perf:
        lt_hr = latest_perf.get("garmin_lt_hr") or latest_perf.get("lactate_threshold_hr")
    if not lt_hr:
        lt_hr = int(max_hr * DEFAULT_LT_HR_FRACTION)

    return {
        "max_hr": int(max_hr),
        "resting_hr": int(resting_hr),
        "lt_hr": int(lt_hr),
        "sex": profile.get("sex") or "male",
    }


def recompute_for_user(
    *,
    user_id: str,
    lookback_days: int = 180,
    write_back_workouts: bool = True,
) -> dict[str, Any]:
    """Recompute per-workout intensity + daily CTL/ATL/TSB/ACWR for one user.

    Returns a summary with counts + the most recent performance point.
    Idempotent — safe to run on a cron schedule.
    """
    client = get_supabase_admin()

    # 1) Pull profile (max_hr, resting_hr, sex) + latest perf snapshot (LT HR).
    profile_resp = (
        client.table("profiles").select("max_hr, resting_hr, sex, date_of_birth")
        .eq("id", user_id).maybe_single().execute()
    )
    profile = profile_resp.data if profile_resp else {}

    perf_resp = (
        client.table("performance_profiles")
        .select("garmin_lt_hr, lactate_threshold_hr")
        .eq("user_id", user_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    latest_perf = perf_resp.data[0] if perf_resp.data else None
    thresholds = _resolve_thresholds(profile or {}, latest_perf)

    # 2) Pull all workouts in the window. We use `started_at` (UTC) so daily
    #    buckets are consistent.
    since = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
    workouts = (
        client.table("workouts")
        .select("id, source, started_at, duration_seconds, avg_hr, trimp, tss")
        .eq("user_id", user_id)
        .gte("started_at", since)
        .order("started_at")
        .execute()
        .data
        or []
    )

    # 3) Compute (or refresh) TRIMP + TSS per workout.
    workout_updates: list[dict] = []
    daily_buckets: dict[date, dict[str, float]] = {}

    for w in workouts:
        trimp = compute_trimp(
            duration_seconds=w["duration_seconds"],
            avg_hr=w.get("avg_hr"),
            max_hr=thresholds["max_hr"],
            resting_hr=thresholds["resting_hr"],
            sex=thresholds["sex"],
        )
        tss = compute_hr_tss(
            duration_seconds=w["duration_seconds"],
            avg_hr=w.get("avg_hr"),
            lt_hr=thresholds["lt_hr"],
        )
        if write_back_workouts and (trimp is not None or tss is not None):
            workout_updates.append({
                "id": w["id"],
                "trimp": trimp,
                "tss": tss,
            })
        if trimp is None and tss is None:
            continue
        day = datetime.fromisoformat(w["started_at"].replace("Z", "+00:00")).date()
        bucket = daily_buckets.setdefault(day, {"tss": 0.0, "trimp": 0.0})
        if tss is not None:
            bucket["tss"] += tss
        if trimp is not None:
            bucket["trimp"] += trimp

    # Persist workout-level TRIMP/TSS. We use update (not upsert) because the
    # workouts row is fully owned by the ingestion path — we just patch two
    # columns per row. With ~50–200 rows the round-trip cost is negligible.
    for upd in workout_updates:
        wid = upd.pop("id")
        client.table("workouts").update(upd).eq("id", wid).execute()

    # 4) Walk the day series from earliest workout → today, computing EMAs even
    #    on rest days (zero-load) so the model stays continuous.
    if not daily_buckets:
        return {
            "status": "no_data",
            "thresholds": thresholds,
            "workouts_scored": 0,
        }

    start_day = min(daily_buckets.keys())
    end_day = date.today()
    series: list[PerformancePoint] = []

    # Initial conditions: zero load → CTL/ATL start at 0. For a brand-new user
    # this is correct. For someone with history, the first ~6 weeks of CTL is
    # a warm-up before the EMA converges — that's expected.
    ctl = 0.0
    atl = 0.0
    cur = start_day
    while cur <= end_day:
        load = daily_buckets.get(cur, {"tss": 0.0, "trimp": 0.0})
        ctl = ctl + ALPHA_CTL * (load["tss"] - ctl)
        atl = atl + ALPHA_ATL * (load["tss"] - atl)
        tsb = ctl - atl
        # ACWR = (last 7d total) / (last 28d total / 4). Compute over `series`.
        acwr = _rolling_acwr(series, cur, load["tss"])
        series.append(PerformancePoint(
            day=cur,
            tss=round(load["tss"], 2),
            trimp=round(load["trimp"], 2),
            ctl=round(ctl, 2),
            atl=round(atl, 2),
            tsb=round(tsb, 2),
            acwr=round(acwr, 3) if acwr is not None else None,
            acwr_zone=_classify_acwr(acwr),
        ))
        cur += timedelta(days=1)

    # 5) Upsert one performance_profiles row per day. We only touch the
    #    load-related columns — Garmin's snapshot fields (VO2max, LT, race
    #    predictions) are preserved on existing rows.
    rows = [{
        "user_id": user_id,
        "snapshot_date": p.day.isoformat(),
        "fitness_ctl": p.ctl,
        "fatigue_atl": p.atl,
        "form_tsb": p.tsb,
        "acwr": p.acwr,
    } for p in series]

    BATCH = 100
    for i in range(0, len(rows), BATCH):
        client.table("performance_profiles").upsert(
            rows[i:i + BATCH], on_conflict="user_id,snapshot_date"
        ).execute()

    latest = series[-1]
    return {
        "status": "ok",
        "thresholds": thresholds,
        "workouts_scored": len(workout_updates),
        "days_computed": len(series),
        "latest": {
            "date": latest.day.isoformat(),
            "ctl": latest.ctl,
            "atl": latest.atl,
            "tsb": latest.tsb,
            "acwr": latest.acwr,
            "acwr_zone": latest.acwr_zone,
        },
    }


def _rolling_acwr(
    prior: list[PerformancePoint], today: date, today_tss: float
) -> float | None:
    """Rolling 7-day acute load / (28-day chronic load / 4)."""
    if len(prior) < 27:   # need at least 28 days incl. today for a sane denominator
        return None
    last_27 = prior[-27:]
    chronic_total = sum(p.tss for p in last_27) + today_tss   # 28 days
    acute_total = sum(p.tss for p in last_27[-6:]) + today_tss   # 7 days
    chronic_avg_weekly = chronic_total / 4.0
    if chronic_avg_weekly < 1e-6:
        return None
    return acute_total / chronic_avg_weekly

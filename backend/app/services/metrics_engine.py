"""Derived performance metrics — VDOT, threshold, economy, fatigue resistance.

Garmin gives us a VO2max and (sometimes) a lactate-threshold HR. Those are
fine but black-box. We compute our own metrics from raw data so we can:
  • Track them over time even when Garmin's auto-detection stays silent
  • Cross-check Garmin's numbers
  • Reason about *why* a metric moved (look at the inputs)

Formulas:

  VDOT (Daniels' running fitness score)
    A single race performance → equivalent VO2max-style number.
    %VO2max(t)   = 0.8 + 0.1894393 * exp(-0.012778 * t)   t in minutes
    %V̇O2(velocity) = -4.60 + 0.182258 * v + 0.000104 * v^2   v in m/min
    VDOT = %V̇O2 / %VO2max
    Source: Daniels' Running Formula, 3rd ed.

  Estimated VO2max (mL/kg/min)
    For race efforts ≥ 5 km: VO2max ≈ VDOT (Daniels treats them as equivalent).
    For shorter or sub-max efforts we fall back to Garmin's number.

  Threshold (LT)
    LT pace ≈ pace from a hard 30–60 min effort (or 88-92% HRmax).
    LT HR ≈ 88% of max HR if we have no better signal, or median HR during
            efforts that lasted 20–60 min at avg HR > 85% max.

  Running economy proxy
    sec_per_km / bpm at z2 efforts. Lower = more efficient (less HR per pace).
    Trend matters more than absolute value.

  Fatigue resistance (0–100)
    100 - clip(mean cardiac drift on long runs, 0, 12) * 8.33
    A 0% drift → 100; a 12% drift → 0.

  Recovery capacity (0–100)
    Median days from peak ATL → TSB > 0 after a high-load week.
    Faster rebound = higher score.
"""

from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.supabase import get_supabase_admin

log = logging.getLogger(__name__)


# Race distances in meters that are valid for VDOT (Daniels uses ≥1500m).
RACE_BANDS = [
    (1500, 1700),   # 1500m
    (1900, 2100),   # 2000m / 2 km
    (4800, 5400),   # 5K
    (9500, 10500),  # 10K
    (14500, 16100), # 15K-10mi
    (20500, 21500), # half marathon
    (41800, 43000), # marathon
]


def compute_all_metrics(*, user_id: str, lookback_days: int = 180) -> dict[str, Any]:
    """Compute all derived metrics for the user and write one snapshot row.

    Writes into today's `performance_profiles` row (upserts on snapshot_date).
    Returns the computed values + the inputs used.
    """
    client = get_supabase_admin()
    today = date.today()
    since_dt = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    # Pull workouts once — every metric reads from the same set.
    workouts = (
        client.table("workouts")
        .select(
            "started_at, sport, duration_seconds, distance_m, avg_hr, max_hr, "
            "avg_pace_s_per_km, hr_zone_seconds, cardiac_drift_pct, pace_decay_pct, "
            "trimp, tss, source"
        )
        .eq("user_id", user_id)
        .gte("started_at", since_dt.isoformat())
        .order("started_at", desc=True)
        .execute()
        .data
        or []
    )

    # Pull thresholds for context.
    profile_resp = (
        client.table("profiles").select("max_hr, resting_hr, weight_kg").eq("id", user_id).maybe_single().execute()
    )
    profile = profile_resp.data if profile_resp else {}
    max_hr = profile.get("max_hr")

    # 1) VDOT + VO2max
    vdot, vdot_inputs = _best_vdot(workouts)

    # 2) Threshold
    lt_pace, lt_hr, lt_inputs = _estimate_threshold(workouts, max_hr=max_hr)

    # 3) Running economy
    re_proxy, re_inputs = _running_economy(workouts)

    # 4) Fatigue resistance
    fr_score, fr_inputs = _fatigue_resistance(workouts)

    # 5) Recovery capacity (uses CTL/ATL series, not workouts)
    rc_score, rc_inputs = _recovery_capacity(user_id, lookback_days=lookback_days)

    inputs_summary = {
        "vdot": vdot_inputs,
        "threshold": lt_inputs,
        "running_economy": re_inputs,
        "fatigue_resistance": fr_inputs,
        "recovery_capacity": rc_inputs,
        "workouts_considered": len(workouts),
    }

    # Upsert today's snapshot — preserves Garmin's snapshot fields (we only
    # write the columns we computed).
    row = {
        "user_id": user_id,
        "snapshot_date": today.isoformat(),
        "vdot": vdot,
        "vo2max_evolverun": vdot,                       # for races ≥5km Daniels treats them as equivalent
        "threshold_pace_s_per_km_evolverun": lt_pace,
        "threshold_hr_evolverun": lt_hr,
        "running_economy_s_per_km_per_bpm": re_proxy,
        "fatigue_resistance_score": fr_score,
        "recovery_capacity_score": rc_score,
        "metrics_inputs": inputs_summary,
    }
    client.table("performance_profiles").upsert(
        row, on_conflict="user_id,snapshot_date"
    ).execute()

    return {
        "as_of": today.isoformat(),
        "metrics": {
            "vdot": vdot,
            "vo2max_evolverun": vdot,
            "threshold_pace_s_per_km": lt_pace,
            "threshold_hr": lt_hr,
            "running_economy_s_per_km_per_bpm": re_proxy,
            "fatigue_resistance_score": fr_score,
            "recovery_capacity_score": rc_score,
        },
        "inputs": inputs_summary,
    }


# ---------------------------------------------------------------------------
# VDOT
# ---------------------------------------------------------------------------
def _best_vdot(workouts: list[dict]) -> tuple[float | None, dict]:
    """Pick the best (fastest pace for distance) running effort in the last 12
    weeks within a known race band and compute VDOT from it.
    """
    candidates = []
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=84)
    for w in workouts:
        if w["sport"] != "running":
            continue
        if not w.get("distance_m") or not w.get("duration_seconds"):
            continue
        dt = datetime.fromisoformat(w["started_at"].replace("Z", "+00:00"))
        if dt < cutoff_dt:
            continue
        dist_m = float(w["distance_m"])
        # Only count steady efforts inside a race band — avoids long slow runs
        # that aren't representative of race fitness.
        for lo, hi in RACE_BANDS:
            if lo <= dist_m <= hi:
                candidates.append({
                    "date": w["started_at"][:10],
                    "distance_m": dist_m,
                    "duration_s": w["duration_seconds"],
                    "vdot": _vdot(dist_m=dist_m, duration_s=w["duration_seconds"]),
                    "source": w.get("source"),
                })
                break

    if not candidates:
        return None, {"reason": "no race-band efforts in last 84 days"}

    # Best = highest VDOT. Dedupe Strava+Garmin pairs by (date, distance) keeping highest.
    best = max(candidates, key=lambda c: c["vdot"] or 0)
    return round(best["vdot"], 2), {
        "best_effort": best,
        "candidates_count": len(candidates),
    }


def _vdot(*, dist_m: float, duration_s: int) -> float | None:
    """Daniels' VDOT formula. Returns ml/kg/min."""
    if dist_m <= 0 or duration_s <= 0:
        return None
    t_min = duration_s / 60.0
    velocity_m_per_min = dist_m / t_min
    # %V̇O2 at race velocity (Daniels' running-economy polynomial)
    pct_vo2_at_v = -4.60 + 0.182258 * velocity_m_per_min + 0.000104 * (velocity_m_per_min ** 2)
    # %VO2max sustainable for duration t
    pct_vo2max = 0.8 + 0.1894393 * math.exp(-0.012778 * t_min) + 0.2989558 * math.exp(-0.1932605 * t_min)
    if pct_vo2max <= 0:
        return None
    return pct_vo2_at_v / pct_vo2max


# ---------------------------------------------------------------------------
# Threshold
# ---------------------------------------------------------------------------
def _estimate_threshold(workouts: list[dict], *, max_hr: int | None) -> tuple[float | None, int | None, dict]:
    """Estimate LT pace + HR.

    LT pace: median pace from 20–60min running efforts at avg HR ≥ 85% max.
    LT HR:   median avg_hr of those same efforts (≈ 88-92% max).
    Falls back to 0.88 * max_hr when no qualifying efforts found.
    """
    if not max_hr:
        return None, None, {"reason": "no max_hr on file"}
    threshold_hr_floor = int(max_hr * 0.85)

    candidates = []
    for w in workouts:
        if w["sport"] != "running":
            continue
        dur = w.get("duration_seconds") or 0
        if dur < 1200 or dur > 3600:   # 20–60 min
            continue
        if not w.get("avg_hr") or w["avg_hr"] < threshold_hr_floor:
            continue
        if not w.get("avg_pace_s_per_km"):
            continue
        candidates.append({
            "date": w["started_at"][:10],
            "duration_s": dur,
            "avg_hr": w["avg_hr"],
            "pace_s_per_km": w["avg_pace_s_per_km"],
        })

    if not candidates:
        return None, int(max_hr * 0.88), {"reason": "no 20-60min hard efforts; using 0.88 * max_hr fallback"}

    # Use median for robustness.
    paces = sorted(float(c["pace_s_per_km"]) for c in candidates)
    hrs = sorted(int(c["avg_hr"]) for c in candidates)
    n = len(candidates)
    lt_pace = paces[n // 2]
    lt_hr = hrs[n // 2]
    return round(lt_pace, 2), int(lt_hr), {
        "n_efforts": n,
        "sample_size_label": "median over qualifying efforts",
    }


# ---------------------------------------------------------------------------
# Running economy
# ---------------------------------------------------------------------------
def _running_economy(workouts: list[dict]) -> tuple[float | None, dict]:
    """RE proxy: median (pace_s_per_km / avg_hr) across z2-dominant runs.

    A z2-dominant run is one where ≥60% of time was in z1+z2 — that's where
    aerobic efficiency dominates and we get a stable HR-pace relationship.
    """
    samples = []
    for w in workouts:
        if w["sport"] != "running":
            continue
        if not w.get("avg_hr") or not w.get("avg_pace_s_per_km"):
            continue
        if not w.get("duration_seconds") or w["duration_seconds"] < 1800:  # ≥30min
            continue
        zones = w.get("hr_zone_seconds") or {}
        total = sum(v for v in zones.values() if isinstance(v, (int, float)))
        easy = (zones.get("z1") or 0) + (zones.get("z2") or 0)
        if total == 0 or easy / total < 0.6:
            continue
        ratio = float(w["avg_pace_s_per_km"]) / float(w["avg_hr"])
        samples.append({"date": w["started_at"][:10], "ratio": round(ratio, 3)})

    if len(samples) < 3:
        return None, {"reason": "need ≥3 z2-dominant runs"}

    ratios = sorted(s["ratio"] for s in samples)
    median = ratios[len(ratios) // 2]
    return round(median, 3), {"n_samples": len(samples), "metric": "median s/km per bpm"}


# ---------------------------------------------------------------------------
# Fatigue resistance
# ---------------------------------------------------------------------------
def _fatigue_resistance(workouts: list[dict]) -> tuple[float | None, dict]:
    """Score 0-100 derived from average aerobic decoupling on long runs.

    We take the absolute cardiac drift % on running efforts ≥15 km and map:
       0%  drift  → 100  (perfect aerobic stability)
       12% drift  → 0    (severe decoupling)
    """
    drifts = []
    for w in workouts:
        if w["sport"] != "running":
            continue
        if (w.get("distance_m") or 0) < 15000:
            continue
        if w.get("cardiac_drift_pct") is None:
            continue
        drifts.append({
            "date": w["started_at"][:10],
            "distance_km": round(float(w["distance_m"]) / 1000, 1),
            "drift_pct": float(w["cardiac_drift_pct"]),
        })

    if not drifts:
        return None, {"reason": "no long runs with decoupling data"}

    # Use the average absolute drift across the last few long runs.
    recent = drifts[:6]   # workouts list is sorted desc
    avg_abs_drift = sum(abs(d["drift_pct"]) for d in recent) / len(recent)
    score = max(0.0, min(100.0, 100 - avg_abs_drift * 8.33))
    return round(score, 2), {
        "n_long_runs": len(recent),
        "avg_abs_drift_pct": round(avg_abs_drift, 2),
    }


# ---------------------------------------------------------------------------
# Recovery capacity
# ---------------------------------------------------------------------------
def _recovery_capacity(user_id: str, *, lookback_days: int) -> tuple[float | None, dict]:
    """Score 0-100 based on days-to-TSB-positive after high-load weeks.

    Algorithm:
      1. Pull daily CTL/ATL/TSB for the window.
      2. Find local peaks in ATL (rolling 14-day max).
      3. For each peak, count days until TSB ≥ 0.
      4. Median rebound time across peaks. Lower median = higher score.
         3 days → 90, 5 days → 70, 7 days → 50, 10+ days → 20.
    """
    client = get_supabase_admin()
    rows = (
        client.table("performance_profiles")
        .select("snapshot_date, fatigue_atl, form_tsb")
        .eq("user_id", user_id)
        .gte("snapshot_date", (date.today() - timedelta(days=lookback_days)).isoformat())
        .order("snapshot_date")
        .execute()
        .data
        or []
    )
    if len(rows) < 30:
        return None, {"reason": "need ≥30 days of TSB data"}

    rebound_days: list[int] = []
    n = len(rows)
    for i in range(7, n - 7):
        atl_i = rows[i].get("fatigue_atl")
        if atl_i is None:
            continue
        # Local 14-day peak check
        window_atls = [r.get("fatigue_atl") or 0 for r in rows[max(0, i - 7) : i + 7]]
        if not window_atls or atl_i < max(window_atls):
            continue
        if atl_i < 30:   # ignore trivially low peaks
            continue
        # Count days from i until TSB ≥ 0
        days = 0
        for j in range(i + 1, n):
            days += 1
            tsb = rows[j].get("form_tsb")
            if tsb is not None and tsb >= 0:
                break
        else:
            continue   # never rebounded inside window — skip
        rebound_days.append(days)

    if not rebound_days:
        return None, {"reason": "no ATL peaks identified in window"}

    rebound_days.sort()
    median = rebound_days[len(rebound_days) // 2]
    # Linear map: 3d→90, 5d→70, 7d→50, 10d→20, clip to 0-100.
    score = max(0.0, min(100.0, 110 - median * 10))
    return round(score, 2), {
        "n_peaks": len(rebound_days),
        "median_rebound_days": median,
    }

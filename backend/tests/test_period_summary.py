"""Regression test for get_period_summary's distance-weighted pace average.

A window whose pace-bearing activities all have null/zero distance used to
divide by zero and crash the tool. It must instead return a clean summary
with avg_pace omitted.
"""

from types import SimpleNamespace

from mcp_server.tools import period_summary


class _Query:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def gte(self, *a, **k):
        return self

    def lte(self, *a, **k):
        return self

    def order(self, *a, **k):
        return self

    def execute(self):
        return SimpleNamespace(data=self._rows)


class _Client:
    def __init__(self, rows):
        self._rows = rows

    def table(self, _name):
        return _Query(self._rows)


def _row(**over):
    base = {
        "started_at": "2026-03-01T08:00:00",
        "sport": "running",
        "source": "strava",
        "distance_m": None,
        "duration_seconds": 1800,
        "avg_hr": 150,
        "avg_pace_s_per_km": 300,
        "avg_power_w": None,
        "cadence_avg": None,
        "elevation_gain_m": None,
        "notes": None,
    }
    base.update(over)
    return base


def _patch(monkeypatch, rows):
    monkeypatch.setattr(period_summary, "get_user_id", lambda: "user-1")
    monkeypatch.setattr(period_summary, "get_supabase_admin", lambda: _Client(rows))


def test_pace_with_zero_distance_does_not_crash(monkeypatch):
    # Both rows have a pace but no usable distance — the old code divided by 0.
    _patch(monkeypatch, [_row(distance_m=None), _row(started_at="2026-03-02T08:00:00", distance_m=0)])
    result = period_summary.get_period_summary("2026-03-01", "2026-03-31", provider="strava")
    assert result["count"] == 2  # did not raise


def test_pace_weighted_average_still_computed(monkeypatch):
    _patch(
        monkeypatch,
        [
            _row(distance_m=10000, avg_pace_s_per_km=300),
            _row(started_at="2026-03-02T08:00:00", distance_m=10000, avg_pace_s_per_km=320),
        ],
    )
    result = period_summary.get_period_summary("2026-03-01", "2026-03-31", provider="strava")
    # Equal distances → simple mean of 300 and 320 = 310 → 5:10/km in the block.
    assert "5:10/km" in result["summary"]

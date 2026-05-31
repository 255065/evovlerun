"""Tests for the Strava webhook event dispatch.

The handler must ack fast: parse the push, resolve the athlete → user, and
schedule a background ingest (or a delete) — without doing the network fetch
inline. These tests mock the user lookup + Supabase client so no DB/network
is touched; they only assert the routing/dispatch decisions.
"""

import pytest
from fastapi import BackgroundTasks

from app.routers import providers

OWNER_ID = 108189954
USER_ID = "11111111-1111-1111-1111-111111111111"
ACTIVITY_ID = 18531785177


class _FakeRequest:
    def __init__(self, payload):
        self._payload = payload

    async def json(self):
        return self._payload


def _event(**over):
    base = {
        "object_type": "activity",
        "object_id": ACTIVITY_ID,
        "aspect_type": "create",
        "owner_id": OWNER_ID,
    }
    base.update(over)
    return base


@pytest.fixture
def known_user(monkeypatch):
    """Athlete OWNER_ID maps to USER_ID."""
    monkeypatch.setattr(
        providers, "find_user_by_provider_id", lambda **k: USER_ID
    )


@pytest.mark.asyncio
async def test_create_schedules_background_ingest(monkeypatch, known_user):
    bt = BackgroundTasks()
    result = await providers.strava_webhook_event(_FakeRequest(_event()), bt)

    assert result == {"status": "received"}
    assert len(bt.tasks) == 1
    task = bt.tasks[0]
    assert task.func is providers._ingest_strava_activity
    assert task.kwargs == {"user_id": USER_ID, "activity_id": str(ACTIVITY_ID)}


@pytest.mark.asyncio
async def test_update_also_ingests(monkeypatch, known_user):
    bt = BackgroundTasks()
    result = await providers.strava_webhook_event(
        _FakeRequest(_event(aspect_type="update")), bt
    )
    assert result == {"status": "received"}
    assert len(bt.tasks) == 1


@pytest.mark.asyncio
async def test_unknown_athlete_is_ignored(monkeypatch):
    monkeypatch.setattr(providers, "find_user_by_provider_id", lambda **k: None)
    bt = BackgroundTasks()
    result = await providers.strava_webhook_event(_FakeRequest(_event()), bt)
    assert result == {"status": "ignored"}
    assert bt.tasks == []


@pytest.mark.asyncio
async def test_non_activity_event_is_ignored(monkeypatch):
    # athlete (deauthorize) events carry object_type="athlete" — nothing to sync.
    bt = BackgroundTasks()
    result = await providers.strava_webhook_event(
        _FakeRequest(_event(object_type="athlete")), bt
    )
    assert result == {"status": "ignored"}
    assert bt.tasks == []


@pytest.mark.asyncio
async def test_delete_event_removes_workout(monkeypatch, known_user):
    deleted = {}

    class _Q:
        def delete(self):
            deleted["delete"] = True
            return self

        def eq(self, col, val):
            deleted[col] = val
            return self

        def execute(self):
            return None

    class _Client:
        def table(self, name):
            deleted["table"] = name
            return _Q()

    monkeypatch.setattr(providers, "get_supabase_admin", lambda: _Client())

    bt = BackgroundTasks()
    result = await providers.strava_webhook_event(
        _FakeRequest(_event(aspect_type="delete")), bt
    )

    assert result == {"status": "received"}
    assert bt.tasks == []  # delete is inline, not backgrounded
    assert deleted["table"] == "workouts"
    assert deleted["source_id"] == str(ACTIVITY_ID)
    assert deleted["user_id"] == USER_ID

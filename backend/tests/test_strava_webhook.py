"""Tests for the Strava webhook event dispatch.

The handler must ack fast: parse the push, resolve the athlete → user, and
schedule a background ingest (or a delete) — without doing the network fetch
inline. These tests mock the user lookup + Supabase client so no DB/network
is touched; they only assert the routing/dispatch decisions.
"""

from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.routers import providers

OWNER_ID = 108189954
USER_ID = "11111111-1111-1111-1111-111111111111"
ACTIVITY_ID = 18531785177
WEBHOOK_TOKEN = "test-webhook-token"


class _FakeRequest:
    def __init__(self, payload, query=None):
        self._payload = payload
        # Default to a valid token so existing routing tests exercise the
        # happy path; auth tests pass query={} or a wrong token explicitly.
        self.query_params = {"token": WEBHOOK_TOKEN} if query is None else query

    async def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def _webhook_secret(monkeypatch):
    """Pin a known webhook verify token so the POST auth gate is deterministic
    regardless of the developer's .env."""
    monkeypatch.setattr(
        providers,
        "get_settings",
        lambda: SimpleNamespace(strava_webhook_verify_token=WEBHOOK_TOKEN),
    )


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


@pytest.mark.asyncio
async def test_missing_token_is_forbidden(monkeypatch):
    """A forged push with no secret token must be rejected before any work —
    this is the fix for the unauthenticated-webhook blocker."""
    monkeypatch.setattr(providers, "find_user_by_provider_id", lambda **k: USER_ID)
    bt = BackgroundTasks()
    with pytest.raises(HTTPException) as exc:
        await providers.strava_webhook_event(
            _FakeRequest(_event(aspect_type="delete"), query={}), bt
        )
    assert exc.value.status_code == 403
    assert bt.tasks == []


@pytest.mark.asyncio
async def test_wrong_token_is_forbidden(monkeypatch):
    monkeypatch.setattr(providers, "find_user_by_provider_id", lambda **k: USER_ID)
    bt = BackgroundTasks()
    with pytest.raises(HTTPException) as exc:
        await providers.strava_webhook_event(
            _FakeRequest(_event(), query={"token": "wrong"}), bt
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_gate_skipped_when_token_unset(monkeypatch):
    """Local dev with no configured token falls open (so the dev tunnel works),
    but production sets the token and is protected."""
    monkeypatch.setattr(
        providers, "get_settings", lambda: SimpleNamespace(strava_webhook_verify_token="")
    )
    monkeypatch.setattr(providers, "find_user_by_provider_id", lambda **k: USER_ID)
    bt = BackgroundTasks()
    result = await providers.strava_webhook_event(_FakeRequest(_event(), query={}), bt)
    assert result == {"status": "received"}

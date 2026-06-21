"""Tests for the Stripe subscription webhook mirror.

Stripe delivers `customer.subscription.created` (status "incomplete") and
`.updated` (status "active") in the same instant and does NOT guarantee order.
The handler must re-fetch the live subscription so a late "created" event can't
regress an already-active subscription back to "incomplete" — which is exactly
what left a paid checkout showing "No plan" in testing.
"""

from types import SimpleNamespace

import stripe

from app.routers import billing

USER_ID = "0a01451f-0000-0000-0000-000000000000"


class _FakeQuery:
    def __init__(self, recorder):
        self._recorder = recorder

    def update(self, payload):
        self._recorder["update"] = payload
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=None)


class _FakeSupabase:
    def __init__(self, recorder):
        self._recorder = recorder

    def table(self, _name):
        return _FakeQuery(self._recorder)


def _active_sub():
    # current_period_end lives on the item in newer API versions — the handler's
    # top-level→item fallback must still pick it up.
    return {
        "id": "sub_test",
        "customer": "cus_test",
        "metadata": {"supabase_user_id": USER_ID},
        "status": "active",
        "current_period_end": None,
        "items": {"data": [{"price": {"id": "price_test"}, "current_period_end": 1784663802}]},
    }


def _stale_created_event():
    # The out-of-order culprit: the payload Stripe sent for subscription.created.
    return {
        "id": "sub_test",
        "customer": "cus_test",
        "metadata": {"supabase_user_id": USER_ID},
        "status": "incomplete",
        "items": {"data": [{"price": {"id": "price_test"}}]},
    }


def test_late_incomplete_event_does_not_regress_active_sub(monkeypatch):
    recorder: dict = {}
    monkeypatch.setattr(billing, "get_supabase_admin", lambda: _FakeSupabase(recorder))
    monkeypatch.setattr(stripe.Subscription, "retrieve", lambda _sid: _active_sub())

    billing._on_subscription_upserted(_stale_created_event())

    assert recorder["update"]["subscription_status"] == "active"
    assert recorder["update"]["subscription_price_id"] == "price_test"
    assert recorder["update"]["subscription_current_period_end"] is not None


def test_falls_back_to_payload_when_refetch_fails(monkeypatch):
    recorder: dict = {}
    monkeypatch.setattr(billing, "get_supabase_admin", lambda: _FakeSupabase(recorder))

    def _boom(_sid):
        raise stripe.StripeError("api down")

    monkeypatch.setattr(stripe.Subscription, "retrieve", _boom)

    # Must not raise; mirrors whatever the event payload carried.
    billing._on_subscription_upserted(_stale_created_event())
    assert recorder["update"]["subscription_status"] == "incomplete"

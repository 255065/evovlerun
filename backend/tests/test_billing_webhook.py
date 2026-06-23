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


class _FakeEmailLookupSupabase:
    """Mirrors the `_FakeSupabase`/`_FakeQuery` shape but also answers the
    `profiles.select("email")` lookup `_email_for_user` needs."""

    def __init__(self, recorder, email="athlete@example.com"):
        self._recorder = recorder
        self._email = email

    def table(self, _name):
        return _FakeEmailLookupQuery(self._recorder, self._email)


class _FakeEmailLookupQuery(_FakeQuery):
    def __init__(self, recorder, email):
        super().__init__(recorder)
        self._email = email

    def select(self, _cols):
        return self

    def limit(self, _n):
        return self

    def execute(self):
        # Serves both the `.update().eq().execute()` chain (return value
        # ignored by the caller) and the `.select().eq().limit().execute()`
        # chain `_email_for_user` reads from.
        return SimpleNamespace(data=[{"email": self._email}])


def test_subscription_deleted_sends_cancellation_email(monkeypatch):
    recorder: dict = {}
    monkeypatch.setattr(billing, "get_supabase_admin", lambda: _FakeEmailLookupSupabase(recorder))
    sent = {}
    monkeypatch.setattr(
        billing,
        "send_email",
        lambda **kwargs: sent.update(kwargs) or "msg_id",
    )

    billing._on_subscription_deleted(
        {"customer": "cus_test", "metadata": {"supabase_user_id": USER_ID}}
    )

    assert recorder["update"]["subscription_status"] == "canceled"
    assert sent["to"] == "athlete@example.com"
    assert "cancelled" in sent["html"]


def test_payment_failed_sends_email(monkeypatch):
    recorder: dict = {}
    monkeypatch.setattr(billing, "get_supabase_admin", lambda: _FakeEmailLookupSupabase(recorder))
    sent = {}
    monkeypatch.setattr(
        billing,
        "send_email",
        lambda **kwargs: sent.update(kwargs) or "msg_id",
    )
    monkeypatch.setattr(
        billing,
        "_user_id_for_customer",
        lambda customer_id, sub_metadata=None: USER_ID,
    )

    billing._on_payment_failed({"customer": "cus_test"})

    assert sent["to"] == "athlete@example.com"
    assert "payment failed" in sent["html"]


def test_notify_does_not_raise_when_send_fails(monkeypatch):
    monkeypatch.setattr(
        billing, "_email_for_user", lambda _user_id: "athlete@example.com"
    )

    def _boom(**_kwargs):
        raise RuntimeError("resend is down")

    monkeypatch.setattr(billing, "send_email", _boom)

    # Must not raise — a notification failure can't fail the webhook.
    billing._notify(USER_ID, "subject", "<p>body</p>")

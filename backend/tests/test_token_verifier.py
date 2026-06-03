"""Tests for the MCP bearer-token verifier's subscription gate.

The MCP connector is the paid product, so verify_token must reject a user
without an active subscription when ENFORCE_SUBSCRIPTION is on — for both the
API-key and the OAuth-JWT token shapes. When enforcement is off, any valid
token resolves (dev / self-use).
"""

import asyncio
from types import SimpleNamespace

from mcp_server import token_verifier as tv

USER_ID = "11111111-1111-1111-1111-111111111111"


def _run(token: str):
    return asyncio.run(tv.EvolveRunTokenVerifier().verify_token(token))


def _settings(*, enforce: bool):
    monkey = SimpleNamespace(enforce_subscription=enforce)
    return lambda: monkey


def test_enforce_off_lets_any_valid_jwt_through(monkeypatch):
    monkeypatch.setattr(tv, "get_settings", _settings(enforce=False))
    monkeypatch.setattr(tv, "decode_access_token", lambda t: {"sub": USER_ID, "scope": "mcp"})
    # Subscription must NOT even be consulted when enforcement is off.
    monkeypatch.setattr(
        tv, "user_has_active_subscription", lambda uid: (_ for _ in ()).throw(AssertionError("checked"))
    )
    result = _run("some.jwt.token")
    assert result is not None
    assert result.client_id == USER_ID


def test_enforce_on_rejects_unsubscribed_jwt(monkeypatch):
    monkeypatch.setattr(tv, "get_settings", _settings(enforce=True))
    monkeypatch.setattr(tv, "decode_access_token", lambda t: {"sub": USER_ID, "scope": "mcp"})
    monkeypatch.setattr(tv, "user_has_active_subscription", lambda uid: False)
    assert _run("some.jwt.token") is None


def test_enforce_on_allows_subscribed_jwt(monkeypatch):
    monkeypatch.setattr(tv, "get_settings", _settings(enforce=True))
    monkeypatch.setattr(tv, "decode_access_token", lambda t: {"sub": USER_ID, "scope": "mcp"})
    monkeypatch.setattr(tv, "user_has_active_subscription", lambda uid: True)
    result = _run("some.jwt.token")
    assert result is not None
    assert result.client_id == USER_ID


def test_enforce_on_rejects_unsubscribed_api_key(monkeypatch):
    monkeypatch.setattr(tv, "get_settings", _settings(enforce=True))
    monkeypatch.setattr(tv, "resolve_user_id", lambda key: USER_ID)
    monkeypatch.setattr(tv, "user_has_active_subscription", lambda uid: False)
    assert _run("evr_abc123") is None


def test_enforce_on_allows_subscribed_api_key(monkeypatch):
    monkeypatch.setattr(tv, "get_settings", _settings(enforce=True))
    monkeypatch.setattr(tv, "resolve_user_id", lambda key: USER_ID)
    monkeypatch.setattr(tv, "user_has_active_subscription", lambda uid: True)
    result = _run("evr_abc123")
    assert result is not None
    assert result.client_id == USER_ID
    assert result.scopes == ["mcp"]


def test_invalid_jwt_still_rejected(monkeypatch):
    monkeypatch.setattr(tv, "get_settings", _settings(enforce=True))
    monkeypatch.setattr(tv, "decode_access_token", lambda t: None)
    assert _run("garbage") is None

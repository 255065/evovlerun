"""OAuth refresh-token tests — the grant Claude.ai uses to silently renew
its 1h access token instead of forcing the user to reconnect."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import oauth as oauth_router
from app.services.oauth_jwt import (
    decode_access_token,
    issue_access_token,
    issue_refresh_token,
    verify_refresh_token,
)

client = TestClient(app)


# ---- service-level: issue / verify ---------------------------------------
def test_refresh_token_round_trip():
    token = issue_refresh_token(user_id="user-1", client_id="client-1", scope="mcp")
    payload = verify_refresh_token(token, expected_client_id="client-1")
    assert payload["sub"] == "user-1"
    assert payload["scope"] == "mcp"
    assert payload["typ"] == "refresh_token"


def test_refresh_verify_rejects_access_token():
    # An access token has the right audience but the wrong `typ`.
    access, _ = issue_access_token(user_id="user-1", client_id="client-1")
    with pytest.raises(ValueError):
        verify_refresh_token(access, expected_client_id="client-1")


def test_refresh_verify_rejects_wrong_client():
    token = issue_refresh_token(user_id="user-1", client_id="client-1")
    with pytest.raises(ValueError):
        verify_refresh_token(token, expected_client_id="other-client")


def test_refresh_verify_rejects_expired():
    token = issue_refresh_token(user_id="user-1", client_id="client-1", ttl_seconds=-1)
    with pytest.raises(ValueError):
        verify_refresh_token(token, expected_client_id="client-1")


def test_refresh_verify_rejects_tampered():
    token = issue_refresh_token(user_id="user-1", client_id="client-1")
    tampered = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    with pytest.raises(ValueError):
        verify_refresh_token(tampered, expected_client_id="client-1")


# ---- endpoint-level: POST /oauth/token  grant_type=refresh_token ----------
@pytest.fixture
def public_client(monkeypatch):
    """Stub the Supabase-backed client lookup with a public PKCE client."""
    monkeypatch.setattr(
        oauth_router, "load_client", lambda cid: {"client_id": cid, "is_public": True}
    )
    monkeypatch.setattr(oauth_router, "touch_client", lambda cid: None)
    # Don't touch the real token store (Supabase) from these tests.
    monkeypatch.setattr(oauth_router, "consume_jti", lambda *a, **k: True)
    monkeypatch.setattr(oauth_router, "is_grant_revoked", lambda *a, **k: False)
    monkeypatch.setattr(oauth_router, "revoke_grant", lambda *a, **k: None)
    return "client-1"


def test_token_endpoint_refreshes_and_rotates(public_client):
    refresh = issue_refresh_token(user_id="user-1", client_id=public_client, scope="mcp")

    resp = client.post(
        "/oauth/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": public_client,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] == 3600
    assert body["scope"] == "mcp"
    # A usable new access token comes back...
    assert decode_access_token(body["access_token"])["sub"] == "user-1"
    # ...alongside a rotated refresh token that also verifies.
    assert verify_refresh_token(body["refresh_token"], expected_client_id=public_client)["sub"] == "user-1"


def test_token_endpoint_rejects_unknown_grant():
    resp = client.post("/oauth/token", data={"grant_type": "password"})
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "unsupported_grant_type"

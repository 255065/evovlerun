"""Auth-code single-use, refresh-token reuse-detection, grant revocation.

Endpoint tests stub the token store (oauth_token_store) via the names imported
into the router; store-unit tests stub the Supabase client directly.
"""

import base64
import hashlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import oauth as oauth_router
from app.services import oauth_token_store as store
from app.services.oauth_jwt import issue_authorization_code, issue_refresh_token

client = TestClient(app)
REDIRECT_URI = "https://claude.ai/api/mcp/auth_callback"
CLIENT_ID = "client-1"


def _s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@pytest.fixture
def stub_client(monkeypatch):
    monkeypatch.setattr(
        oauth_router, "load_client", lambda cid: {"client_id": cid, "is_public": True}
    )
    monkeypatch.setattr(oauth_router, "touch_client", lambda cid: None)
    monkeypatch.setattr(oauth_router, "is_grant_revoked", lambda *a, **k: False)
    return monkeypatch


# ---- auth-code single use -------------------------------------------------
def test_auth_code_replay_is_rejected(stub_client):
    verifier = "verifier-xyz-0123456789"
    code = issue_authorization_code(
        user_id="user-1", client_id=CLIENT_ID, redirect_uri=REDIRECT_URI,
        scope="mcp", code_challenge=_s256(verifier), code_challenge_method="S256",
    )
    # First redemption consumes the jti, second sees it already spent.
    seen: set[str] = set()

    def fake_consume(jti, **k):
        if jti in seen:
            return False
        seen.add(jti)
        return True

    stub_client.setattr(oauth_router, "consume_jti", fake_consume)

    data = {
        "grant_type": "authorization_code", "code": code,
        "redirect_uri": REDIRECT_URI, "client_id": CLIENT_ID, "code_verifier": verifier,
    }
    first = client.post("/oauth/token", data=data)
    second = client.post("/oauth/token", data=data)
    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"]["detail"] == "code already used"


# ---- refresh reuse detection ----------------------------------------------
def test_refresh_reuse_revokes_grant(stub_client):
    refresh = issue_refresh_token(user_id="user-1", client_id=CLIENT_ID, scope="mcp")
    revoked = {}
    stub_client.setattr(oauth_router, "consume_jti", lambda *a, **k: False)  # already spent
    stub_client.setattr(
        oauth_router, "revoke_grant", lambda u, c: revoked.update({"u": u, "c": c})
    )

    resp = client.post(
        "/oauth/token",
        data={"grant_type": "refresh_token", "refresh_token": refresh, "client_id": CLIENT_ID},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["detail"] == "refresh token reuse"
    assert revoked == {"u": "user-1", "c": CLIENT_ID}


def test_refresh_on_revoked_grant_is_rejected(stub_client):
    refresh = issue_refresh_token(user_id="user-1", client_id=CLIENT_ID, scope="mcp")
    stub_client.setattr(oauth_router, "is_grant_revoked", lambda *a, **k: True)
    stub_client.setattr(oauth_router, "consume_jti", lambda *a, **k: True)

    resp = client.post(
        "/oauth/token",
        data={"grant_type": "refresh_token", "refresh_token": refresh, "client_id": CLIENT_ID},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["detail"] == "grant revoked"


# ---- /oauth/revoke --------------------------------------------------------
def test_revoke_endpoint_revokes_grant(stub_client):
    refresh = issue_refresh_token(user_id="user-1", client_id=CLIENT_ID, scope="mcp")
    revoked = {}
    stub_client.setattr(
        oauth_router, "revoke_grant", lambda u, c: revoked.update({"u": u, "c": c})
    )

    resp = client.post("/oauth/revoke", data={"token": refresh, "client_id": CLIENT_ID})
    assert resp.status_code == 200
    assert resp.json() == {"revoked": True}
    assert revoked == {"u": "user-1", "c": CLIENT_ID}


# ---- store unit: failure posture ------------------------------------------
class _RaisingInsert:
    def __init__(self, exc):
        self._exc = exc

    def insert(self, *_a, **_k):
        return self

    def execute(self):
        raise self._exc


class _Client:
    def __init__(self, exc):
        self._exc = exc

    def table(self, _n):
        return _RaisingInsert(self._exc)


def test_consume_jti_duplicate_returns_false(monkeypatch):
    err = Exception("duplicate key value violates unique constraint")
    monkeypatch.setattr(store, "get_supabase_admin", lambda: _Client(err))
    assert store.consume_jti("jti-1", typ="auth_code", user_id="u", client_id="c") is False


def test_consume_jti_other_error_fails_open(monkeypatch):
    err = Exception('relation "oauth_consumed_tokens" does not exist')
    monkeypatch.setattr(store, "get_supabase_admin", lambda: _Client(err))
    # Infra error must not lock users out — allow.
    assert store.consume_jti("jti-1", typ="auth_code", user_id="u", client_id="c") is True


def test_consume_jti_no_jti_allows(monkeypatch):
    # Older tokens without a jti are allowed (nothing to track).
    assert store.consume_jti(None, typ="refresh_token", user_id="u", client_id="c") is True

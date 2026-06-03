"""PKCE enforcement tests.

OAuth 2.1 requires every authorization-code flow to use PKCE (S256). These
tests pin that we (a) reject an authorize request without an S256 challenge,
and (b) reject a code at exchange time if it carries no challenge (downgrade)
or the verifier doesn't match.
"""

import base64
import hashlib

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import oauth as oauth_router
from app.services.oauth_jwt import decode_access_token, issue_authorization_code

client = TestClient(app)

REDIRECT_URI = "https://claude.ai/api/mcp/auth_callback"
CLIENT_ID = "client-1"


def _s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@pytest.fixture
def public_client(monkeypatch):
    monkeypatch.setattr(
        oauth_router, "load_client", lambda cid: {"client_id": cid, "is_public": True}
    )
    monkeypatch.setattr(oauth_router, "redirect_uri_allowed", lambda c, uri: True)
    monkeypatch.setattr(oauth_router, "touch_client", lambda cid: None)
    return CLIENT_ID


# ---- /authorize -----------------------------------------------------------
def test_authorize_rejects_missing_pkce(public_client):
    resp = client.get(
        "/oauth/authorize",
        params={"response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI},
        follow_redirects=False,
    )
    assert resp.status_code == 400


def test_authorize_rejects_plain_method(public_client):
    resp = client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code_challenge": _s256("v"),
            "code_challenge_method": "plain",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 400


def test_authorize_accepts_s256(public_client):
    resp = client.get(
        "/oauth/authorize",
        params={
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code_challenge": _s256("verifier-123"),
            "code_challenge_method": "S256",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302  # redirect to the consent screen


# ---- /token  grant_type=authorization_code --------------------------------
def _exchange(code: str, verifier: str | None):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
    }
    if verifier is not None:
        data["code_verifier"] = verifier
    return client.post("/oauth/token", data=data)


def test_auth_code_exchange_succeeds_with_valid_verifier(public_client):
    verifier = "the-original-code-verifier-string-1234567890"
    code = issue_authorization_code(
        user_id="user-1",
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope="mcp",
        code_challenge=_s256(verifier),
        code_challenge_method="S256",
    )
    resp = _exchange(code, verifier)
    assert resp.status_code == 200
    assert decode_access_token(resp.json()["access_token"])["sub"] == "user-1"


def test_auth_code_exchange_rejects_wrong_verifier(public_client):
    code = issue_authorization_code(
        user_id="user-1",
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope="mcp",
        code_challenge=_s256("right-verifier"),
        code_challenge_method="S256",
    )
    resp = _exchange(code, "wrong-verifier")
    assert resp.status_code == 400


def test_auth_code_exchange_rejects_downgrade_without_challenge(public_client):
    # A code minted with no challenge (the downgrade attack) must be refused
    # even when no verifier is sent.
    code = issue_authorization_code(
        user_id="user-1",
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope="mcp",
        code_challenge=None,
        code_challenge_method=None,
    )
    resp = _exchange(code, None)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "invalid_grant"

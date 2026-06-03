"""Tests for the /oauth/deny endpoint — open-redirect prevention."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

GOOD_CLIENT = {
    "client_id": "test-client",
    "client_name": "Test App",
    "redirect_uris": ["https://example.com/callback"],
    "is_public": True,
}


def test_deny_valid_redirect(monkeypatch):
    from app.routers import oauth as oauth_router
    monkeypatch.setattr(oauth_router, "load_client", lambda cid: GOOD_CLIENT if cid == "test-client" else None)
    monkeypatch.setattr(
        oauth_router,
        "redirect_uri_allowed",
        lambda client, uri: uri in client["redirect_uris"],
    )

    resp = client.post(
        "/oauth/deny",
        json={
            "client_id": "test-client",
            "redirect_uri": "https://example.com/callback",
            "state": "abc123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "error=access_denied" in data["redirect_url"]
    assert "state=abc123" in data["redirect_url"]
    assert data["redirect_url"].startswith("https://example.com/callback")


def test_deny_unknown_redirect_uri_rejected(monkeypatch):
    """An unregistered redirect_uri must be refused — no open redirect."""
    from app.routers import oauth as oauth_router
    monkeypatch.setattr(oauth_router, "load_client", lambda cid: GOOD_CLIENT if cid == "test-client" else None)
    monkeypatch.setattr(
        oauth_router,
        "redirect_uri_allowed",
        lambda client, uri: uri in client["redirect_uris"],
    )

    resp = client.post(
        "/oauth/deny",
        json={
            "client_id": "test-client",
            "redirect_uri": "https://attacker.example.com/steal",
            "state": "",
        },
    )
    assert resp.status_code == 400


def test_deny_unknown_client_rejected(monkeypatch):
    from app.routers import oauth as oauth_router
    monkeypatch.setattr(oauth_router, "load_client", lambda cid: None)

    resp = client.post(
        "/oauth/deny",
        json={
            "client_id": "nonexistent",
            "redirect_uri": "https://example.com/callback",
            "state": "",
        },
    )
    assert resp.status_code == 400

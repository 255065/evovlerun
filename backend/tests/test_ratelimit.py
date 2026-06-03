"""Rate limiting on public endpoints.

Hammers /oauth/register past its per-IP limit and asserts the backstop kicks
in with 429. register_client is stubbed so no Supabase write happens.
"""

from app.main import app
from app.routers import oauth as oauth_router
from fastapi.testclient import TestClient

client = TestClient(app)


def test_register_is_rate_limited(monkeypatch):
    monkeypatch.setattr(
        oauth_router,
        "register_client",
        lambda **k: {"client_id": "c", "client_name": k.get("client_name")},
    )
    body = {"redirect_uris": ["https://claude.ai/api/mcp/auth_callback"]}

    statuses = [client.post("/oauth/register", json=body).status_code for _ in range(12)]

    # Limit is 10/minute — the first calls succeed, then we get 429s.
    assert 200 in statuses
    assert 429 in statuses
    assert statuses.index(429) >= 10

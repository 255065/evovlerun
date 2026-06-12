"""OAuth discovery metadata consistency.

Strict MCP clients (ChatGPT) read the authorization server from the
protected-resource document, then fetch that server's metadata and require
its `issuer` to be byte-identical to the discovered URL. A trailing-slash
mismatch makes ChatGPT fail with "something went wrong"; Claude tolerates it.
These tests lock the two documents together so the mismatch can't regress.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_issuer_matches_advertised_authorization_server():
    pr = client.get("/.well-known/oauth-protected-resource").json()
    asrv = client.get("/.well-known/oauth-authorization-server").json()
    # The string a client follows from protected-resource must equal the
    # issuer string the auth-server metadata returns — exactly.
    assert pr["authorization_servers"] == [asrv["issuer"]]


def test_issuer_has_trailing_slash_like_fastmcp():
    """FastMCP normalises the issuer with a trailing slash; ours must match."""
    asrv = client.get("/.well-known/oauth-authorization-server").json()
    assert asrv["issuer"].endswith("/")


def test_endpoints_have_no_double_slash():
    asrv = client.get("/.well-known/oauth-authorization-server").json()
    for key in ("authorization_endpoint", "token_endpoint", "registration_endpoint"):
        # e.g. https://host/oauth/authorize — scheme's // is the only one.
        assert asrv[key].count("//") == 1, f"{key} = {asrv[key]}"

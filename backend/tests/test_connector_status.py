"""GET /mcp-keys/status — "has this user ever connected Claude via OAuth?".

The signal is any row in oauth_consumed_tokens for the user (auth-code
redemption or refresh rotation both write one). A missing table (migration
0008 not applied yet) must degrade to not-connected, never a 500.
"""

from types import SimpleNamespace

from app.routers import mcp_keys


class _Query:
    def __init__(self, rows, raise_on_execute=False):
        self._rows = rows
        self._raise = raise_on_execute

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def execute(self):
        if self._raise:
            raise RuntimeError('relation "oauth_consumed_tokens" does not exist')
        return SimpleNamespace(data=self._rows)


class _Client:
    def __init__(self, rows, raise_on_execute=False):
        self._rows = rows
        self._raise = raise_on_execute

    def table(self, _name):
        return _Query(self._rows, self._raise)


_USER = SimpleNamespace(id="user-1")


def test_connected_when_consumed_token_row_exists(monkeypatch):
    monkeypatch.setattr(mcp_keys, "get_supabase_admin", lambda: _Client([{"jti": "abc"}]))
    assert mcp_keys.connector_status(_USER).claude_connected is True


def test_not_connected_when_no_rows(monkeypatch):
    monkeypatch.setattr(mcp_keys, "get_supabase_admin", lambda: _Client([]))
    assert mcp_keys.connector_status(_USER).claude_connected is False


def test_missing_table_degrades_to_not_connected(monkeypatch):
    monkeypatch.setattr(
        mcp_keys, "get_supabase_admin", lambda: _Client([], raise_on_execute=True)
    )
    assert mcp_keys.connector_status(_USER).claude_connected is False

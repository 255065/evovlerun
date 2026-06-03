"""replace_window must scope deletes to the target plan, not all user plans."""

from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture()
def mock_supabase():
    client = MagicMock()

    # Existing active plan
    plan_row = {"id": "plan-A", "race_type": "marathon", "race_date": None, "philosophy": "polarized"}
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        plan_row
    ]

    # Delete returns some deleted rows
    delete_chain = MagicMock()
    delete_chain.data = [{"id": "w1"}, {"id": "w2"}]
    (
        client.table.return_value.delete.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.execute
    ).return_value = delete_chain

    # Insert returns inserted rows
    insert_result = MagicMock()
    insert_result.data = [{"id": "new1"}]
    client.table.return_value.insert.return_value.execute.return_value = insert_result

    return client, plan_row["id"]


def test_replace_window_scopes_to_plan(mock_supabase):
    """The delete chain must include .eq('plan_id', plan_id)."""
    client, plan_id = mock_supabase

    with (
        patch("mcp_server.tools.plan_crud.get_supabase_admin", return_value=client),
        patch("mcp_server.tools.plan_crud.get_user_id", return_value="user-1"),
    ):
        from mcp_server.tools import plan_crud

        result = plan_crud.save_training_plan(
            sessions=[
                {"scheduled_date": "2026-06-10", "session_type": "easy"},
                {"scheduled_date": "2026-06-11", "session_type": "long"},
            ],
            mode="replace_window",
            window_start="2026-06-10",
            window_end="2026-06-11",
        )

    assert result.get("ok") is True

    # Verify that somewhere in the delete chain .eq was called with plan_id.
    delete_mock = client.table.return_value.delete.return_value
    # Walk the .eq() call chain and collect all (field, value) pairs.
    all_eq_calls = []
    chain = delete_mock
    while True:
        calls = chain.eq.call_args_list if hasattr(chain.eq, "call_args_list") else []
        for c in calls:
            all_eq_calls.append(c.args if c.args else tuple(c.kwargs.values()))
        if hasattr(chain, "eq") and chain.eq.return_value is not chain:
            chain = chain.eq.return_value
            break
        break

    # The assertion: plan_id must appear somewhere in the eq() calls.
    # We check by inspecting the mock's call tree for 'plan_id' field.
    all_calls_str = str(client.table.return_value.delete.mock_calls)
    assert "plan_id" in all_calls_str, (
        "replace_window delete did not scope to plan_id — "
        "would wipe workouts from other plans"
    )
    assert plan_id in all_calls_str

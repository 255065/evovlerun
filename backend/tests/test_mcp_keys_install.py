"""The MCP-key install snippet must target the hosted server (mcp-remote),
not a local repo clone."""

from app.routers import mcp_keys


def test_install_snippet_is_hosted():
    snip = mcp_keys._build_install_snippets("evr_testkey123")

    # Hosted: mcp-remote against the public /mcp URL, key as a Bearer header.
    assert "mcp-remote" in snip.claude_desktop_config_snippet
    assert "evr_testkey123" in snip.claude_desktop_config_snippet
    assert snip.mcp_url.endswith("/mcp")

    # No trace of the old local-clone approach.
    for blob in (snip.claude_desktop_config_snippet, snip.macos_install_script):
        assert "run_mcp.sh" not in blob
        assert "clone" not in blob.lower()


def test_install_script_checks_for_node():
    snip = mcp_keys._build_install_snippets("evr_k")
    assert "npx" in snip.macos_install_script

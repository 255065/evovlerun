#!/bin/bash
# Wrapper der starter MCP-serveren med korrekt cwd, så både
# `mcp_server` modulet og `.env` indlæses fra backend-mappen.

cd "$(dirname "$0")"
exec ./.venv/bin/python -m mcp_server.server "$@"

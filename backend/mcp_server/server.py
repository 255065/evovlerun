"""MCP server entry point.

Run as:
    EVOLVERUN_API_KEY=evr_... python -m mcp_server.server               # stdio
    EVOLVERUN_API_KEY=evr_... python -m mcp_server.server streamable    # HTTP

Stdio is the right mode for Claude Desktop and Claude Code. Streamable HTTP is
how a hosted MCP marketplace listing will eventually run.
"""

from __future__ import annotations

import argparse
import logging
import sys

from mcp.server.fastmcp import FastMCP

from mcp_server.context import bind_user_from_env
from mcp_server.tools import activities, plans, recovery


def build_server() -> FastMCP:
    mcp = FastMCP(
        name="EvolveRun",
        instructions=(
            "EvolveRun is the user's personal endurance training data. "
            "Tools expose activities, recovery (sleep/HRV/body battery/readiness), "
            "planned workouts, and the user's physiological performance snapshot. "
            "All numbers are scoped to the authenticated user — never invent values. "
            "When answering, prefer to cite specific data points and explain the "
            "physiological reasoning rather than just stating prescriptions."
        ),
    )

    # ---- Activities & training volume ----
    mcp.tool(
        name="list_activities",
        description="List the user's recent activities (runs, rides, swims, strength, etc.).",
    )(activities.list_activities)
    mcp.tool(
        name="get_activity",
        description="Return the full record (including splits/laps) for one activity by id.",
    )(activities.get_activity)
    mcp.tool(
        name="get_training_volume",
        description="Aggregate training load over a window: total km, hours, sessions, per-sport breakdown.",
    )(activities.get_training_volume)

    # ---- Recovery / wellness ----
    mcp.tool(
        name="get_recovery_snapshot",
        description="Latest recovery state (sleep, HRV, readiness, body battery) plus deltas vs. the user's 7-day baseline.",
    )(recovery.get_recovery_snapshot)
    mcp.tool(
        name="get_sleep",
        description="Sleep history for the last N days: per-night hours + score and the window average.",
    )(recovery.get_sleep)
    mcp.tool(
        name="get_hrv_trend",
        description="HRV (rMSSD) per day with a 7-day rolling baseline — useful for spotting multi-day drops that signal overtraining.",
    )(recovery.get_hrv_trend)

    # ---- Plans & performance ----
    mcp.tool(
        name="get_planned_workouts",
        description="Upcoming structured workouts from the user's active training plan (with rationale per session).",
    )(plans.get_planned_workouts)
    mcp.tool(
        name="get_current_plan",
        description="Summary of the user's active plan: race goal, current phase, philosophy, week-of-plan.",
    )(plans.get_current_plan)
    mcp.tool(
        name="get_performance_summary",
        description="Latest physiological snapshot — CTL/ATL/TSB/ACWR — plus the current detected limiter.",
    )(plans.get_performance_summary)

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="EvolveRun MCP server")
    parser.add_argument(
        "transport",
        nargs="?",
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="MCP transport (default: stdio for Claude Desktop).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,  # stdio transport uses stdout — keep logs off it
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    bind_user_from_env()
    server = build_server()
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()

"""MCP server entry point.

Two transports:

  stdio (default — Claude Desktop):
      EVOLVERUN_API_KEY=evr_… python -m mcp_server.server
  HTTP (hosted, multi-user — claude.ai / ChatGPT):
      python -m mcp_server.server http
      ↳ Listens on :8001 by default. Each request must carry
        `Authorization: Bearer evr_…`; the token verifier resolves it to a
        user_id and our tools scope their queries to that user.

The HTTP variant is also embedded inside the FastAPI app at /mcp — see
app/main.py — which means in production we serve API + MCP on one port.

Tool surface
------------
We deliberately ship a small, Chirona-matching toolkit (11 tools) so the
chat assistant does the reasoning and we only expose raw data shapes. All
tool names use kebab-case to match Chirona's visual fingerprint inside
Claude.ai's connector picker. Behind the scenes our richer analytics
(limiter engine, metrics engine, post-workout AI, etc.) still run in the
sync pipeline — they're just not callable from chat. If we ever want them
back as chat tools, re-register the entries below.
"""

import argparse
import logging
import os
import sys

from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings

from mcp_server.context import bind_user_from_env
from mcp_server.token_verifier import EvolveRunTokenVerifier
from mcp_server.tools import (
    activities,
    conversation_init,
    latest,
    period_summary,
    plan_crud,
    plans,
)


INSTRUCTIONS = """EvolveRun gives you read+write access to the user's real endurance training data.

MANDATORY BEHAVIOR — read carefully, this overrides defaults:

1. On EVERY user message that involves their training, health, or any
   coaching question, your FIRST action MUST be to call
   `conversation-initialisation-critical-instructions`. It returns the
   coaching guide that defines tone, response shape, and when to use which
   tool. Do NOT answer from general knowledge before calling it.

2. NEVER fabricate training data. If the user asks "how was my last run",
   "what's my volume this month", "how have I slept lately" — you MUST
   call the matching get-* tool. Don't invent numbers.

3. When the user asks you to design or build a training plan
   (any wording: "lav mig en plan", "build me a week", "suggest 7 days",
   "træningsplan"), follow this exact sequence:
     a. Call `conversation-initialisation-critical-instructions` (guide).
     b. Call `get-period-summary` for the last 4-6 weeks to understand
        their current volume + fitness.
     c. Call `get-latest-run` and `get-latest-sleep` for current state.
     d. Call `get-planned-workouts` to see if they already have a plan.
     e. Propose the plan in chat with concrete sessions per day.
     f. ASK: "Do you want me to save this to EvolveRun? Append, or
        replace the window from <start> to <end>?"
     g. Only after the user confirms, call `save-training-plan`.
     h. Quote the returned dashboard_url in your reply so they can see it.

4. All numbers are scoped to the authenticated user. You cannot see other
   users' data. If a tool returns empty, say so — don't invent a placeholder.

Tools available: conversation-initialisation-critical-instructions,
get-recent-activities, get-activity-details, get-run-splits,
get-period-summary, get-latest-run, get-latest-sleep, get-latest-body,
get-planned-workouts, push-planned-workout, save-training-plan,
delete-planned-workout."""


def build_server(token_verifier: TokenVerifier | None = None) -> FastMCP:
    """Construct the FastMCP server with the 11 production tools registered.

    Args:
        token_verifier: Pass an instance to enable HTTP Bearer auth.
            For stdio mode, leave None — auth happens once via env var.
    """
    auth_settings = None
    if token_verifier is not None:
        public_url = os.environ.get("MCP_PUBLIC_URL", "http://localhost:8000")
        auth_settings = AuthSettings(
            issuer_url=public_url,
            resource_server_url=f"{public_url.rstrip('/')}/mcp",
            required_scopes=["mcp"],
        )

    mcp = FastMCP(
        name="EvolveRun",
        instructions=INSTRUCTIONS,
        token_verifier=token_verifier,
        auth=auth_settings,
        stateless_http=True,
        streamable_http_path="/",
        host="0.0.0.0",
        port=8001,
    )

    # ── 1. Coaching guide — must be called first on every user turn ──
    mcp.tool(
        name="conversation-initialisation-critical-instructions",
        description=(
            "READ ME FIRST on every user message. Returns the EvolveRun coaching guide: "
            "tone, response shape, when to merge providers, which tool to prefer for which "
            "question. Call this once per user turn before any other EvolveRun tool."
        ),
    )(conversation_init.conversation_initialisation_critical_instructions)

    # ── 2-6. Read tools — activities ──
    mcp.tool(
        name="get-recent-activities",
        description=(
            "List the user's recent activities (runs, rides, swims, strength, etc.) "
            "with summary metrics. Use for 'show me my last N workouts' style questions."
        ),
    )(activities.list_activities)

    mcp.tool(
        name="get-activity-details",
        description=(
            "Return the full record for one activity by id — distance, time, pace, "
            "HR (avg + max), cadence, power, elevation, cardiac drift, pace decay, "
            "polarized score, HR-zone breakdown, weather, raw provider payload."
        ),
    )(activities.get_activity)

    mcp.tool(
        name="get-run-splits",
        description=(
            "Per-lap breakdown for one activity — HR, pace, cadence, power, elevation "
            "per split. Use to spot cardiac drift, pace decay, or verify whether a "
            "structured workout hit its prescribed splits."
        ),
    )(activities.get_activity_splits)

    mcp.tool(
        name="get-period-summary",
        description=(
            "Compact aggregate stats for a date window — counts, totals, weighted-average "
            "pace, mean HR/cadence/power, total elevation, longest single activity. "
            "Args: startDate (YYYY-MM-DD), endDate (YYYY-MM-DD), runOnly (bool, optional), "
            "provider (\"garmin\"/\"strava\"/\"all\", optional, default 'all' which dedupes "
            "Strava↔Garmin twins). Use for 'how much did I run last month' style questions."
        ),
    )(period_summary.get_period_summary)

    # ── 7-9. Point-lookup latest-X tools ──
    mcp.tool(
        name="get-latest-run",
        description=(
            "Return the user's most recent running activity with all key metrics "
            "(distance, pace, HR, cadence, power, elevation, training effect, "
            "cardiac drift, polarized score, HR-zone breakdown)."
        ),
    )(latest.get_latest_run)

    mcp.tool(
        name="get-latest-sleep",
        description=(
            "Return last night's sleep (duration, score, HRV, resting HR, readiness, "
            "body battery, SpO2) plus the 7-day rolling baseline so deviations are obvious."
        ),
    )(latest.get_latest_sleep)

    mcp.tool(
        name="get-latest-body",
        description=(
            "Return the user's most recent body composition snapshot — weight, body fat %, "
            "muscle mass, plus profile fields (height, sex, age, max HR, resting HR)."
        ),
    )(latest.get_latest_body)

    # ── 10. Planned workouts read ──
    mcp.tool(
        name="get-planned-workouts",
        description=(
            "Upcoming structured workouts from the user's active training plan, with "
            "per-session rationale, target zones, prescribed pace/distance/duration."
        ),
    )(plans.get_planned_workouts)

    # ── 11. Single-session write ──
    mcp.tool(
        name="push-planned-workout",
        description=(
            "Add ONE planned workout to the user's active training plan. "
            "For multi-day plans, prefer `save-training-plan` (bulk + atomic). "
            "Args: scheduled_date (YYYY-MM-DD), session_type (easy/long/tempo/threshold/"
            "intervals/vo2max/fartlek/hills/recovery/race/strength/cross_training/rest), "
            "sport (default 'running'), duration_min, distance_m, description, rationale."
        ),
    )(plan_crud.push_planned_workout)

    # ── 12. Bulk plan write (the centerpiece for assistant-generated plans) ──
    mcp.tool(
        name="save-training-plan",
        description=(
            "Save a multi-session training plan the assistant proposed. ALWAYS confirm "
            "with the user before calling. Two modes: `append` keeps the existing plan "
            "and adds the new sessions; `replace_window` first deletes every planned "
            "workout in [window_start, window_end] and inserts the new ones — use this "
            "when the user said 'update my plan' or 'overwrite next week'. Returns "
            "`dashboard_url` so you can tell the user where to see the plan."
        ),
    )(plan_crud.save_training_plan)

    # ── 13. Single-session delete ──
    mcp.tool(
        name="delete-planned-workout",
        description=(
            "Remove a planned workout by its id. Use when the athlete asks to drop a "
            "session, or when overwriting one specific day (delete first, then push)."
        ),
    )(plan_crud.delete_planned_workout)

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="EvolveRun MCP server")
    parser.add_argument(
        "transport",
        nargs="?",
        default="stdio",
        choices=["stdio", "sse", "streamable-http", "http"],
        help="MCP transport. Use 'stdio' for Claude Desktop, 'http' for hosted multi-user.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger("mcp_server")

    transport = args.transport
    if transport == "http":
        transport = "streamable-http"

    if transport == "stdio":
        log.info("Starting MCP server in stdio mode")
        bind_user_from_env()
        server = build_server()
        server.run(transport="stdio")
    else:
        log.info("Starting MCP server in %s mode on :8001", transport)
        server = build_server(token_verifier=EvolveRunTokenVerifier())
        server.run(transport=transport)


if __name__ == "__main__":
    main()

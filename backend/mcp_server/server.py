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
"""

from __future__ import annotations

import argparse
import logging
import sys

import os

from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings

from mcp_server.context import bind_user_from_env
from mcp_server.token_verifier import EvolveRunTokenVerifier
from mcp_server.tools import activities, limiter, metrics, performance, plans, recovery


INSTRUCTIONS = (
    "EvolveRun is the user's personal endurance training data. "
    "Tools expose activities, recovery (sleep/HRV/body battery/readiness), "
    "planned workouts, the user's physiological performance snapshot, our "
    "computed metrics (VDOT, threshold, running economy, fatigue resistance), "
    "the AI-detected limiter, and per-key-session post-workout AI debriefs. "
    "All numbers are scoped to the authenticated user — never invent values. "
    "When answering, prefer to cite specific data points and explain the "
    "physiological reasoning rather than just stating prescriptions."
)


def build_server(token_verifier: TokenVerifier | None = None) -> FastMCP:
    """Construct the FastMCP server with all tools registered.

    Args:
        token_verifier: Pass an instance to enable HTTP Bearer auth.
            For stdio mode, leave None — auth happens once via env var.
    """
    # FastMCP refuses to take a token_verifier without an AuthSettings — even
    # for pure Bearer-token flows where the OAuth metadata is unused. We
    # publish a placeholder issuer that points to the public deployment URL
    # (overridable via MCP_PUBLIC_URL for staging/local).
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
        # Stateless = each HTTP request is independent. Simpler to deploy
        # behind a load balancer and matches our tool-call model (no session
        # state between calls).
        stateless_http=True,
        # Bind to all interfaces so containers/Cloud Run can route to us.
        host="0.0.0.0",
        port=8001,
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
    mcp.tool(
        name="get_activity_splits",
        description="Per-lap breakdown for one activity — HR, pace, cadence, power, elevation. Use to spot cardiac drift, pace decay, or verify if a structured workout hit its targets.",
    )(activities.get_activity_splits)

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

    # ---- Deep performance baseline (Garmin's own estimates) ----
    mcp.tool(
        name="get_performance_baseline",
        description="Garmin's physiological estimates: VO2max, lactate threshold (HR + pace), race predictions (5k/10k/HM/M), training status (productive/peaking/overreaching), endurance & hill scores, fitness age, FTP. Use to ground intensity/goal recommendations in actual ceilings.",
    )(performance.get_performance_baseline)
    mcp.tool(
        name="get_personal_records",
        description="The user's personal records from Garmin (best 5k, 10k, half marathon, marathon, longest run, biggest climb, best power efforts). Use when discussing realistic race goals or progression.",
    )(performance.get_personal_records)
    mcp.tool(
        name="get_stress_trend",
        description="Daily stress (Garmin all-day stress) + body battery + SpO2 over a window. High stress compounding with training load = elevated illness/injury risk.",
    )(performance.get_stress_trend)
    mcp.tool(
        name="get_zone_distribution",
        description="Aggregate time-in-HR-zones across all workouts in a window, plus polarized-training compliance score (% in z1+z2 vs. z4+z5). Use to verify whether the user's training is actually polarized vs. stuck in the moderate-intensity 'grey zone'.",
    )(performance.get_zone_distribution)
    mcp.tool(
        name="get_fitness_timeline",
        description="Daily CTL (fitness) / ATL (fatigue) / TSB (form) / ACWR (injury risk) series — the Banister/Coggan-style training load model. Use to assess fitness trend, detect overreaching (high ATL + negative TSB), or judge readiness for a hard block.",
    )(performance.get_fitness_timeline)

    # ---- Limiter engine ----
    mcp.tool(
        name="get_current_limiter",
        description="Latest AI-detected primary limiter (aerobic_capacity / lactate_threshold / muscular_endurance / running_economy / anaerobic_capacity / recovery / neuromuscular) with confidence, evidence, physiology explanation, and recommended training focus. Use to justify session prescriptions or explain training direction.",
    )(limiter.get_current_limiter)
    mcp.tool(
        name="get_limiter_history",
        description="All limiter determinations in a window — shows whether the athlete's bottleneck has shifted over time.",
    )(limiter.get_limiter_history)

    # ---- Derived metrics + trends + post-workout AI ----
    mcp.tool(
        name="get_athlete_metrics",
        description="EvolveRun's own derived metrics: VDOT, VO2max estimate, threshold pace+HR, running economy proxy (s/km per bpm), fatigue resistance (0-100), recovery capacity (0-100). Use to ground recommendations in athlete-specific physiology.",
    )(metrics.get_athlete_metrics)
    mcp.tool(
        name="get_metric_trends",
        description="4 / 8 / 12-week trend cards for every key metric (VO2max, CTL, HRV, sleep, threshold pace, running economy, fatigue resistance, weekly volume, polarized %). Each card includes direction, delta %, and whether the move is good for that metric.",
    )(metrics.get_metric_trends)
    mcp.tool(
        name="get_post_workout_briefings",
        description="Recent AI-generated debriefs for key sessions (long runs, intervals, threshold, race) with verdict, what-went-well, watch-outs, and next-session adjustment.",
    )(metrics.get_post_workout_briefings)

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
        stream=sys.stderr,  # stdio uses stdout for the protocol — keep logs off it
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger("mcp_server")

    transport = args.transport
    # 'http' is a friendly alias.
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

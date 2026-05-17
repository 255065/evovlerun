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
from mcp_server.tools import activities, limiter, metrics, performance, plans, recovery


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

    # ---- Limiter engine (AI-detected physiological constraints) ----
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

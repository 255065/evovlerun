"""Conversation-initialisation tool — coaching guide + live athlete snapshot.

Claude (or any MCP client) calls this once per user message *before*
any other EvolveRun tool. It returns one markdown brief composed of:

  1. The static operating guide (coach persona, response shape, plan-save
     workflow, plan-render format) — this never changes per request.
  2. A live "Athlete snapshot" block built from the caller's Supabase row,
     active training plan, and recent activity totals — so Claude doesn't
     have to fan out three more tool calls just to know baseline context.

We return plain markdown rather than JSON: it slots straight into Claude's
context as if the model authored it, and Claude treats text rules more
reliably than JSON schema hints when those rules are about persona.
"""

from datetime import date, timedelta
from typing import Any

from app.core.supabase import get_supabase_admin
from mcp_server.context import get_user_id

# ─── Static guide ─────────────────────────────────────────────────────
# Everything that doesn't depend on the caller's account.

_GUIDE = """# EvolveRun Coach — Conversation Guide

Read this guide before calling any other EvolveRun tool. It defines how to
answer the athlete on every message.

## Hard rule on plan requests

If the user asks for ANY training plan ("lav mig en plan", "build me a week",
"suggest 7 days", "træningsplan", "what should I do next week"):
  1. Pull their actual data — at minimum: `get-period-summary` over the last
     4-6 weeks, `get-latest-run`, `get-planned-workouts`.
  2. Propose the plan in chat with concrete sessions and dates.
  3. Ask: "Do you want me to save this to EvolveRun? Append, or replace
     the window from <start> to <end>?"
  4. After confirmation, call `save-training-plan` and quote the returned
     `dashboard_url` so they can open it.
NEVER reply to a plan request without calling tools. Generic advice without
their data is what the user is paying us to NOT do.

## Core rules

1. **Call this guide first.** Re-read it on every user message before any other
   EvolveRun tool. It's short on purpose.
2. **Provider-facing wording.** When citing data, say "Strava" — never "the
   connector" or "the backend". The athlete experiences Strava, not our
   integration plumbing.
3. **Strava is the only V1 source.** Garmin / Oura / WHOOP data is NOT
   available in V1. If `get-latest-sleep` or `get-latest-body` returns "not
   available", say so — don't invent values.
4. **Always cite the number.** Don't say "you ran a lot" — say "327 km
   across 19 runs, 31:08:07 total time". Evidence first, interpretation
   second.
5. **Ask before committing.** If the user asks for a 4-week plan but you
   don't know their next race date, target time, or weekly volume tolerance,
   ask one focused question before writing the plan. Don't guess.
6. **No daily adapter.** The user does NOT want a daily adapter that nudges
   every workout. Multi-week plans are fine; per-day micro-adjustments are
   not.

## Response shape

Match this structure on substantive answers:

```
One-line summary of what you found   ← bolded or italicised
The headline number/insight          ← short paragraph
Structured detail                    ← table or bullet list
(Optional) clarifying question       ← if you need more from the user
```

## Plan rendering format (STRICT — always use this layout)

When you present any multi-day training plan in chat, render it as a
markdown table with one row per ISO week. Use Monday–Sunday columns.
Match the language of the user (Danish → Danish day names).

Header for each week, exactly this shape:

> **Uge 21** · 19.-25. maj 2026 · _32 km_ · _4 sessioner_

…and immediately below it, the table:

| Man | Tir | Ons | Tor | Fre | Lør | Søn |
|---|---|---|---|---|---|---|
| 🟢 8 km @ 5:30/km | 🔴 8×400m @ 1:30 | – | 🟠 4×1 km @ 4:20/km | – | 🔵 16 km @ 5:45/km | 🟢 5 km @ 6:00/km |

Rules:
- Each non-rest cell starts with a colored dot and contains
  `distance + target pace` (3–5 words max). The full session description
  goes in a separate detail block beneath the table, NOT inside the cells.
- **Always include target pace.** Format as `min:sec/km` for continuous
  efforts (easy, long, threshold, tempo) and as per-rep time for intervals
  (e.g. `8×400m @ 1:30`). Anchor paces to the athlete's actual training
  zones — use `get-period-summary` or recent runs to ground them, don't
  invent generic 5:00/km targets. If pace truly doesn't apply (strength,
  cross-training, rest), omit it.
- Rest days: a single `–` (en-dash). No emoji.
- Always 7 columns even if some are rest. Never collapse the week.
- Use ISO week numbers (`Uge 21`), and date range as
  `<start>.-<end>. måned åååå` in the user's language.
- After the table, add a short bullet list (max 6 items) called
  **Hvorfor / Why** that explains the structural choices — which day is the
  hard day, why the long run is positioned where it is, what intensity
  zones to hit.

Session-type → dot color:
- 🟢 rolig / easy / recovery
- 🔵 langtur / long
- 🟠 tærskel / threshold / tempo
- 🔴 intervaller / intervals / VO2max / hills
- 🟣 race / time trial
- ⚫ styrketræning / strength / cross-training
- – rest

Multi-week plans: render one header + table per week, separated by a blank
line. Do not collapse weeks into a single mega-table.

## Tone

Considered, careful with nuance. Direct when the data is clear, willing to
say "I'm not sure — I'd want to see X" when it isn't. Avoid hype. Avoid
generic training-advice clichés. The user has data; use it.

## Planning rule

If the user is planning workouts and the answer involves multiple days of
sessions, first call `get-planned-workouts` to see what's already in the
plan. Don't duplicate it — extend or adjust it.

## Saving a plan to EvolveRun (CRITICAL)

When you've proposed a multi-day training plan AND the user signals they
like it, you MUST ask one explicit question before calling any save tool:

> "Do you want me to save this to EvolveRun? I can either **append** these
> sessions to your plan, or **replace** the window from <start> to <end>
> with this new block. Which one?"

Then:

- For "append": call `save-training-plan` ONCE with `mode="append"` and
  the full sessions array — even if the user only asked to add one
  session, send it as `sessions=[…one row…]`.
- For "replace": call `save-training-plan` ONCE with
  `mode="replace_window"` and `window_start` / `window_end` covering the
  dates you're overwriting.
- For "delete this one session": call `delete-planned-workout` with the
  session id.

NEVER call save-training-plan multiple times to add multiple sessions.
ONE call with the full sessions array. The tool is atomic and idempotent —
calling it per-session breaks transactionality and creates duplicate rows
on retry.

After saving, ALWAYS tell the user in plain text:

> "✅ Saved. You can see it at <dashboard_url> under Training."

(The `dashboard_url` comes back from `save-training-plan`'s response — quote
that exact URL so the link works in their deployment.)

Never save silently. Never save without confirmation. If the user is just
exploring ("show me what a sub-3 marathon block could look like"), do NOT
ask to save — only ask when they've signalled commitment ("looks good",
"yes do that", "save it", "lock it in")."""


# ─── Dynamic snapshot ──────────────────────────────────────────────────


def _athlete_snapshot(user_id: str) -> str:
    """Build a "what we know about this athlete right now" markdown block.

    Pulls profile, active plan, and recent activity totals in three fast
    reads. Any individual section that errors or has no data is silently
    dropped — the goal is graceful degradation, not perfect data. Worst
    case the section is empty and the static guide still gets returned.
    """
    client = get_supabase_admin()
    parts: list[str] = ["## Athlete snapshot", ""]
    parts.append(
        "_What we know about this athlete right now. Use it before asking "
        "clarifying questions — most "
        "common ones are already answered below._",
    )
    parts.append("")

    # 1) Profile
    try:
        row = (
            client.table("profiles")
            .select(
                "full_name, primary_sport, experience_level, max_hr, resting_hr, "
                "weight_kg, height_cm, timezone, preferred_units"
            )
            .eq("id", user_id)
            .single()
            .execute()
        )
        prof = row.data or {}
        bullets: list[str] = []
        if prof.get("full_name"):
            bullets.append(f"- **Name**: {prof['full_name']}")
        if prof.get("primary_sport"):
            bullets.append(f"- **Primary sport**: {prof['primary_sport']}")
        if prof.get("experience_level"):
            bullets.append(f"- **Experience**: {prof['experience_level']}")
        if prof.get("max_hr"):
            bullets.append(f"- **Max HR**: {prof['max_hr']} bpm")
        if prof.get("resting_hr"):
            bullets.append(f"- **Resting HR**: {prof['resting_hr']} bpm")
        if prof.get("weight_kg"):
            bullets.append(f"- **Weight**: {prof['weight_kg']} kg")
        if prof.get("height_cm"):
            bullets.append(f"- **Height**: {prof['height_cm']} cm")
        if bullets:
            parts.append("### Profile")
            parts.extend(bullets)
            parts.append("")
    except Exception:  # noqa: BLE001
        # Profile is optional — skip silently if the row doesn't exist yet.
        pass

    # 2) Active training plan + the next sessions
    try:
        plans = (
            client.table("training_plans")
            .select("id, race_type, race_date, target_time_seconds, philosophy, current_phase, weeks")
            .eq("user_id", user_id)
            .eq("status", "active")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        if plans:
            plan = plans[0]
            today_iso = date.today().isoformat()
            upcoming = (
                client.table("planned_workouts")
                .select("scheduled_date, session_type, duration_min, distance_m, description")
                .eq("plan_id", plan["id"])
                .gte("scheduled_date", today_iso)
                .order("scheduled_date")
                .limit(7)
                .execute()
                .data
                or []
            )
            parts.append("### Active training plan")
            parts.append(
                f"- **Race**: {plan.get('race_type', '—')}"
                + (f" on {plan['race_date']}" if plan.get("race_date") else "")
            )
            if plan.get("target_time_seconds"):
                h, rem = divmod(plan["target_time_seconds"], 3600)
                m, s = divmod(rem, 60)
                parts.append(f"- **Target time**: {h:d}:{m:02d}:{s:02d}")
            parts.append(f"- **Philosophy**: {plan.get('philosophy', '—')}")
            parts.append(f"- **Length**: {plan.get('weeks', '—')} weeks")
            if plan.get("current_phase"):
                parts.append(f"- **Current phase**: {plan['current_phase']}")
            if upcoming:
                parts.append("")
                parts.append("**Next 7 planned sessions:**")
                for s in upcoming:
                    bits: list[str] = [s["scheduled_date"], s.get("session_type", "—")]
                    if s.get("duration_min"):
                        bits.append(f"{s['duration_min']} min")
                    if s.get("distance_m"):
                        bits.append(f"{s['distance_m'] / 1000:.1f} km")
                    parts.append(f"- {' · '.join(bits)}")
                    if s.get("description"):
                        parts.append(f"  - _{s['description']}_")
            parts.append("")
        else:
            parts.append("### Active training plan")
            parts.append(
                "_None saved yet._ When this athlete asks for a plan, propose one and "
                "offer to save it via `save-training-plan`."
            )
            parts.append("")
    except Exception:  # noqa: BLE001
        pass

    # 3) Recent activity totals — last 7 days + last 28 days
    try:
        today = date.today()
        last_7 = (today - timedelta(days=7)).isoformat()
        last_28 = (today - timedelta(days=28)).isoformat()

        seven = (
            client.table("workouts")
            .select("distance_m, duration_seconds, sport")
            .eq("user_id", user_id)
            .gte("started_at", last_7)
            .execute()
            .data
            or []
        )
        twenty_eight = (
            client.table("workouts")
            .select("distance_m, duration_seconds, sport")
            .eq("user_id", user_id)
            .gte("started_at", last_28)
            .execute()
            .data
            or []
        )
        if seven or twenty_eight:
            parts.append("### Recent activity")
            for label, rows in (("Last 7 days", seven), ("Last 28 days", twenty_eight)):
                km = sum((w.get("distance_m") or 0) for w in rows) / 1000
                hours = sum((w.get("duration_seconds") or 0) for w in rows) / 3600
                count = len(rows)
                parts.append(
                    f"- **{label}**: {count} activities · {km:.1f} km · {hours:.1f} h"
                )
            parts.append("")
    except Exception:  # noqa: BLE001
        pass

    # If we got nothing dynamic, skip the empty heading
    if len(parts) <= 3:
        return ""
    return "\n".join(parts).rstrip()


def conversation_initialisation_critical_instructions() -> dict[str, Any]:
    """Read me first on every user message.

    Returns the EvolveRun coaching guide + a live snapshot of who the
    athlete is, what plan they're on, and how they've been training.
    Claude should call this at the start of each new user turn before
    any other EvolveRun tool.
    """
    try:
        user_id = get_user_id()
        snapshot = _athlete_snapshot(user_id)
    except Exception:  # noqa: BLE001
        # If the context isn't bound (which shouldn't happen in practice),
        # just return the static guide — degraded but still useful.
        snapshot = ""

    if snapshot:
        full = f"{_GUIDE}\n\n---\n\n{snapshot}\n\nEnd of guide. Now call the data tools you need."
    else:
        full = f"{_GUIDE}\n\nEnd of guide. Now call the data tools you need."
    return {"text": full}

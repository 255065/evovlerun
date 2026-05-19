# CLAUDE.md — Project Instructions
# Project Name: EvolveRun (adaptive performance OS for endurance athletes)

## Mission (Version 1)

**Simple AI endurance coach. Connect Strava. Get answers.**

V1 ships as a single-purpose product: a hosted MCP connector that lets
Claude.ai / ChatGPT / Gemini answer questions about a runner's actual
Strava data, plus a thin web app for billing, onboarding, and viewing
the AI-generated training plan.

We deliberately do NOT in V1:
- Run our own LLM (the chat assistant does the reasoning)
- Integrate Garmin / Oura / Whoop / Polar directly (Strava is the aggregator)
- Build daily briefings or daily-adapter features (rejected by founder)
- Compete on dashboards or unified-health graphs

We DO in V1:
- Strava OAuth + webhook + 90-day initial sync + live updates
- 11 MCP tools (Chirona-parity, kebab-case) exposed via streamable HTTP
- Coaching-guide tool that locks tone, response shape, and plan grid format
- `save-training-plan` as the single atomic plan-write tool
- Hosted OAuth 2.1 + PKCE so claude.ai's "Add custom connector" → Connect
  flow works end-to-end
- Marketing landing page (`/`) — signups go straight to `/dashboard`
- Stripe Checkout subscription from day 1 (~€9–14/mo, no free tier)
- (5-question onboarding wizard rolled back — deferred to V2 once we have
  a place to surface the answers, e.g. into the coaching-guide tool)

## V2 mission (after first paying customers retain)

Expand the data graph (Garmin partner API, Oura, WHOOP), add an
explainability layer ("why this session?"), and run heavier analytics
(limiter engine, 4-week Opus reviews) for premium tiers. Long-term:
"verdens mest intelligente adaptive AI-træningscoach" stays the north
star; V1 is the wedge.

## Core philosophy
- Combine real sport science (Daniels, Hansons, Pfitzinger, Norwegian /
  Polarized, Canova, Lydiard) with live data and AI.
- Everything must be **explanatory** — the user has to understand "why".
- Safety first: conservative progression, no dangerous load spikes.
- Simple beats sophisticated. The MCP chat assistant does the heavy
  reasoning; our job is clean data + tight tool descriptions.

## Tech stack (strict)
- **Frontend**: Next.js 16 (App Router) + TypeScript + Tailwind +
  shadcn/ui + Radix. Deployed to Vercel.
- **Backend**: Python 3.13 + FastAPI. Deployed to Railway.
- **Database**: Supabase (PostgreSQL + Auth + Storage). RLS on every
  user-scoped table.
- **AI (V1)**: None directly. The MCP connector lets the user's own
  Claude/ChatGPT/Gemini account do the reasoning over our data tools.
  All onboard-LLM code (Anthropic + MiniMax clients, plan_generator,
  limiter_engine, post_workout_engine) was removed in V1 cleanup —
  bringing it back is the V2 hook for premium analytics features.
- **Integrations (V1)**: Strava only. We "inherit" Garmin/Apple/Polar/
  Coros/Suunto/Wahoo because they all auto-sync to Strava.
- **Integrations (V2)**: Garmin official partner, Oura, WHOOP, Polar
  AccessLink — all gratis OAuth, no aggregator.
- **Payments**: Stripe Checkout, subscription model.
- **Email**: Resend (deferred — needed before public launch).
- **Cron**: Railway scheduled jobs (deferred — performance recompute
  runs after each sync today, that's enough for V1).

## Repo layout
```
evolverun/
├── frontend/        Next.js 16 app  (Vercel)
├── backend/         FastAPI service (Railway, port 8000)
│   └── mcp_server/  MCP tools mounted at /mcp on the same FastAPI app
├── supabase/        SQL migrations + config
├── docs/            ARCHITECTURE.md, ROADMAP.md, DEPLOY.md
└── CLAUDE.md        This file
```

## Production URLs
- Backend / MCP: `https://evovlerun-production.up.railway.app`
- Frontend: `https://evovlerun.vercel.app`
- MCP endpoint: `https://evovlerun-production.up.railway.app/mcp`
- GitHub: `255065/evovlerun` (note: 3 v's in the name — typo, can be
  renamed later without breaking anything)

## Coding rules
- Think step-by-step before coding. Don't speculatively refactor.
- Clean, modular, well-named identifiers. Comment only when the WHY is
  non-obvious.
- TypeScript strict on frontend.
- Security-first: encrypt all provider tokens with Fernet, never log
  secrets, RLS on every user-scoped Supabase table.
- Tests where they catch real regressions.
- Errors propagate; don't swallow them silently.

## MCP tool surface (V1 — locked at 11 tools)
1. `conversation-initialisation-critical-instructions` — coaching guide
2. `get-recent-activities`
3. `get-activity-details`
4. `get-run-splits`
5. `get-period-summary` — Chirona-parity aggregate
6. `get-latest-run`
7. `get-latest-sleep` — Strava has no sleep → returns "not available" in V1
8. `get-latest-body` — Strava has no body comp → ditto
9. `get-planned-workouts`
10. `save-training-plan` — only plan-write tool, atomic, batch-friendly
11. `delete-planned-workout`

Adding tools: don't. The chat assistant is doing fine with 11. If we
need more, expand `save-training-plan`'s argument schema instead of
adding a 12th tool. LLM tool-selection accuracy collapses above ~15
tools.

## Role / persona
You are both a senior full-stack developer AND a sport scientist /
endurance coach. Be proactive about technical refactors, tooling, and
product instincts — but never sneak in features the founder didn't ask
for. Especially:
- ❌ Don't propose a Daily Adapter (founder rejected)
- ❌ Don't propose Terra integration in V1 (cost-blocked)
- ❌ Don't propose new MCP tools without explicit ask

## Physiology knowledge
Cardiac drift, pace decay, running economy, ACWR, HRV, lactate threshold,
zone-2 training, training methodologies (Daniels, Hansons, Pfitzinger,
Norwegian, Polarized, Canova, Lydiard) and their strengths / weaknesses.
Use this when reasoning about *what the user should ask the chat
assistant*, not to author training advice yourself — that's the LLM's job.

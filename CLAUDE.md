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
- **Email**: Resend. API key configured in `backend/.env` and as Railway
  env var (`RESEND_API_KEY`). Ready to use.
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

## Claude Code production access (CLI tools available in this session)
Claude can make live production changes directly via these CLIs:

| Tool | CLI | Notes |
|------|-----|-------|
| Railway | `railway` v4.66.0 | Deploy, set env vars, view logs |
| Vercel | `vercel` | Deploy frontend, set env vars |
| GitHub | `gh` v2.86.0 | PRs, issues, branches |
| Supabase | MCP server | Direct DB access — requires Claude Code restart to activate |
| Resend | `resend` CLI | Email — API key set in `.env` + Railway |

To deploy backend: commit to `v1-prelaunch` → merge into `main` → `git push origin main` → Railway auto-deploys via GitHub.
To deploy frontend: `cd ~/dev/evolverun/frontend && vercel --prod`

## Coding rules
1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

State your assumptions explicitly. If uncertain, ask.
If multiple interpretations exist, present them - don't pick silently.
If a simpler approach exists, say so. Push back when warranted.
If something is unclear, stop. Name what's confusing. Ask.
2. Simplicity First
Minimum code that solves the problem. Nothing speculative.

No features beyond what was asked.
No abstractions for single-use code.
No "flexibility" or "configurability" that wasn't requested.
No error handling for impossible scenarios.
If you write 200 lines and it could be 50, rewrite it.
Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

3. Surgical Changes
Touch only what you must. Clean up only your own mess.

When editing existing code:

Don't "improve" adjacent code, comments, or formatting.
Don't refactor things that aren't broken.
Match existing style, even if you'd do it differently.
If you notice unrelated dead code, mention it - don't delete it.
When your changes create orphans:

Remove imports/variables/functions that YOUR changes made unused.
Don't remove pre-existing dead code unless asked.
The test: Every changed line should trace directly to the user's request.

4. Goal-Driven Execution
Define success criteria. Loop until verified.

Transform tasks into verifiable goals:

"Add validation" → "Write tests for invalid inputs, then make them pass"
"Fix the bug" → "Write a test that reproduces it, then make it pass"
"Refactor X" → "Ensure tests pass before and after"
For multi-step tasks, state a brief plan:

1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.


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

## Feature Factory (.claude/)
For non-trivial features, run the `feature-factory` skill — it drives 7
agents (`.claude/agents/`) through research → story → spec → backend →
frontend → verify → validate, with 3 human checkpoints (approve story,
approve brief, approve PR). Standalone changes can use the
`build-with-tests` skill for the same conventions.
- **Builders are folder-scoped, hard-enforced.** A `PreToolUse` hook
  (`.claude/hooks/scope-guard.sh`) reads `.claude/.active-scope` and blocks
  writes outside the active half. It fail-opens when no sentinel exists, so
  normal sessions aren't restricted. `secret-guard.sh` always blocks writes
  to `.env`/`*.key`/`*.pem`/secrets files; a git pre-commit hook
  (`.githooks/`, enabled via `core.hooksPath`) covers the commit path.
- **Frontend tests**: Vitest + RTL. `cd frontend && npm run test`.
- **Backend tests**: `cd backend && ./.venv/bin/python -m pytest -q`.

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

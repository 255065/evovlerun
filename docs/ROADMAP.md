# Roadmap

## Status (2026-05-18)

EvolveRun er live i production. Backend på Railway, frontend på Vercel, Claude.ai connector OAuth fungerer. Hele Notion-paritet for installation er opnået — brugere kan paste vores MCP URL i Claude.ai → Settings → Connectors → "Connect" og er logget ind med OAuth + PKCE.

## Hvad der er færdigt ✅

### Infrastruktur
- ✅ Monorepo frontend (Next.js 16) + backend (FastAPI) + Supabase
- ✅ 5 migrationer kørt: initial schema, mcp_api_keys, Garmin deep data, metrics engine, OAuth clients
- ✅ Railway production deploy m. Docker, --proxy-headers, healthcheck
- ✅ Vercel production deploy m. korrekte env-vars
- ✅ Encrypted token storage (Fernet)
- ✅ Auth gating via Supabase + JWT
- ✅ HTTPS overalt + CORS for Claude.ai

### Data ingestion (Module 1)
- ✅ Strava OAuth + webhook
- ✅ Garmin (python-garminconnect) deep sync — splits, HR zones, weather, performance snapshots, PRs
- ✅ Auto-detect history start (paginerer Garmin's activity list, sync helt tilbage til ældste)
- ✅ Profile sync (DOB, sex, vægt, max HR observed)
- ✅ Batched upserts (50 per chunk) — survive Supabase statement timeout
- ✅ Phase-isolated sync (én fejl dræber ikke resten)

### Performance Model + Limiter Engine (Module 2)
- ✅ Banister TRIMP + Coggan hrTSS per workout
- ✅ Daglig CTL/ATL/TSB/ACWR EMA-rollup
- ✅ Limiter detection engine (Claude Opus / MiniMax-M2.5 deep tier)
- ✅ LLM abstraction (`app/services/llm/`) — provider-agnostic Anthropic ↔ MiniMax
- ✅ MiniMax-M2.5 som aktiv provider via OpenAI SDK + custom base URL

### Metrics + Trends (Module 2 udvidet)
- ✅ VDOT (Daniels), VO2max estimat, threshold pace+HR, running economy proxy
- ✅ Fatigue resistance score, recovery capacity score
- ✅ 4/8/12-ugers trend cards på 14 metrics
- ✅ Chart-ready aggregates (`get_easy_run_trend`, `compare_periods`)

### Training Plan Generator (Module 3)
- ✅ 2-stage plan generator (blueprint + ugevis ekspansion)
- ✅ Auto-philosophy valg (Daniels/Pfitzinger/Hansons/Norwegian/polarized/Lydiard/auto-hybrid)
- ✅ Per-session rationale med data-citater

### Post-workout AI
- ✅ Auto-debriefs for key sessions (long runs ≥15km, intervals, threshold, race)
- ✅ Idempotent (workout_id key på briefing)
- ✅ Verdict + what-went-well + watch-outs + næste-session-justering

### MCP server (Module 5 — bonus)
- ✅ 24 MCP tools eksponeret via streamable HTTP transport
- ✅ Bearer token + OAuth 2.1 + PKCE — fungerer i Claude Desktop, Cursor, Code, OG Claude.ai web
- ✅ Dynamic Client Registration (RFC 7591)
- ✅ Konversation-initialisation tool (Chirona-style coaching guide)
- ✅ `get_period_summary` — Chirona-equivalent compact aggregat
- ✅ Discovery metadata på root (RFC 9728)

### Frontend
- ✅ Login, signup, beskyttet dashboard
- ✅ Connections-side med Strava OAuth + Garmin login + sync-knapper (30d, 90d, all-time auto)
- ✅ MCP-keys side med 3-step onboarding (auto-install bash, manual JSON, ChatGPT placeholder)
- ✅ OAuth consent screen (`/oauth/consent`) for Claude.ai-flow
- ✅ Træningsside med plan + plan-form
- ✅ Limiter-side
- ✅ Profile-side
- ✅ Format helpers, sparkline, badges, sessioner-cards

## Næste milestone — Chirona-style polish

Detaljeret spec i `~/.claude/projects/-Users-valdemarstoerum/memory/chirona_pattern.md`.

### M8: 5-spørgsmåls onboarding wizard (3-5 dage)
- [ ] `/onboarding` welcome screen — serif headline, warm beige bg, orange accent
- [ ] Q01 Goal-vælger (8 cards, "Most Picked" badge)
- [ ] Q01b conditional follow-ups (race event details, swim focus, etc.)
- [ ] Q02 Sessions/hours slider med auto-løb-label (Light/Steady/Committed/Heavy)
- [ ] Q03 Connector-vælger (genbrug eksisterende provider-rows)
- [ ] Q04 Style-vælger (Structured/Free-flow/Adaptive/Hybrid)
- [ ] Q05 AI coach pick (Claude/ChatGPT med example chat preview)
- [ ] Dark final-review screen "Looks good. Ready when you are."
- [ ] Auto-trigger plan_generator efter Q5
- [ ] Middleware gate: unfinished users → `/onboarding`
- [ ] DB: `onboarding_completed_at` + `onboarding_responses` jsonb table

### M9: Cookbook (1-2 dage)
- [ ] `/dashboard/cookbook` side med to tabs (Common questions / Prompt patterns)
- [ ] 10 baked prompts implementeret (specifikke prompts i chirona_pattern.md)
- [ ] Monospace `PROMPT` block med Copy-knap per kort
- [ ] One-line "when to use this" hint per prompt

### M10: Tool-rename til kebab-case (½ dag)
- [ ] Omdøb 24 tools til `provider-action` format (`garmin-list-activities`, `strava-get-recent`)
- [ ] Source-prefix på tools der er provider-specifikke
- [ ] Behold internal Python-navne (kun MCP tool names ændres)

### M11: Dark theme dashboard (2-3 dage)
- [ ] Dark warm-charcoal radial bg (`#1A1612 → #0E0B0A`)
- [ ] Orange accent (`#DC6B3F`)
- [ ] Tre-tier layout: CONNECTED SOURCES + AI COACH + ADD ANOTHER
- [ ] Provider rows med live syncing-pill + dropdown + Disconnect
- [ ] AI coach rows med "Add Claude" / "Set up ChatGPT"-knapper

### M12: Pricing + Stripe (2-3 dage)
- [ ] Stripe Checkout integration
- [ ] Pro Quarterly tier (£9.99 / 3 mdr eller £4.99/mdr eller similar)
- [ ] Account-side med plan-overview + "View billing"
- [ ] Free-trial logic (fx 14 dage)

### M13: Flere providers (officielle gratis APIs) — VENTER
- [ ] Apply til Garmin Connect Developer Program (gratis, 2 dages approval) — fix uofficielt API risk
- [ ] Oura officiel OAuth
- [ ] WHOOP officiel OAuth
- [ ] Polar AccessLink OAuth
- [ ] Suunto OAuth
- [ ] (Senere) COROS officielt API

### M14: 4-week Review (Module 4)
- [ ] Cron job hver 28. dag → Opus deep analysis
- [ ] Output i `coach_briefings` med type `4_week_review`
- [ ] Email via Resend (kræver M15)

### M15: Email + cron — VENTER
- [ ] Resend integration
- [ ] Daily briefings via Haiku (HVIS brugeren beder om det — daily adapter er eksplicit afvist)
- [ ] Cron worker (Railway scheduled jobs eller Vercel cron)

## Eksplicit afvist

- ❌ **Daily Adapter** — brugeren afslog dette eksplicit ("det er for meget justering"). Plans er fine, micro-adjustments per dag er det ikke.
- ❌ **Terra-aggregator nu** — for dyrt ($399-499/mo). Venter til 50+ paying users gør det rentabelt. Indtil da bruger vi officielle gratis OAuth APIs direkte (M13).

## Differentierings-idéer fra original roadmap

Stadig relevante hvis vi vil ud over Chirona-paritet:

1. **Explainability Replay** — klik "vis mig hvorfor" på enhver session og få filosofi-citat + de seneste 3 ugers data der triggerede sessionen
2. **Physiological Digital Twin** — confidence intervals + sub-3:30 marathon-forecast med sandsynlighed
3. **HRV-baseret overtrænings-prediction** — 7-dages glidende baseline der dropper >5% i 5+ dage = alert
4. **Race Pace Strategy AI** — GPX + vejrprognose + brugerens pacing-historie → per-km plan
5. **Hybrid Philosophy Engine** — automatisk filosofi-skift per fase i stedet for én filosofi for hele planen
6. **Voice journaling → indsigt** — Whisper + Haiku ekstraherer subjektive signaler
7. **Form Analyzer** — slow-mo video + Pose-detection
8. **Community benchmarking** — anonymiserede peers
9. **Coach Personality Selector** — Maria (empatisk) / Marius (direkte) / Pheidippides (klassisk)
10. **Injury Risk Score** — kombineret ACWR + decoupling + sleep-debt + biomekanik

Ingen af disse ligger forrest — først skal vi have Chirona-paritet (M8-M12).

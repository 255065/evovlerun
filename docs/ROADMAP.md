# Roadmap

## Pivot — Version 1 strategy (2026-05-19)

**Version 1 = "AI insights from your Strava data."** Strip everything that
isn't Strava + the MCP chat surface. Ship paying-customer-ready in 1–2
weeks instead of 2 months. Reasons:

- Strava is the de-facto aggregator — Garmin / Apple Watch / Polar /
  COROS / Suunto / Wahoo all auto-sync there. We "inherit" ~85% of the
  endurance market without paying Terra ($400+/mo) or waiting on
  Garmin's partner program.
- The intelligence layer is **the chat assistant** (Claude.ai / ChatGPT
  via our MCP connector). We don't run an LLM ourselves in V1. That
  drops infrastructure, latency, and per-user LLM cost to ~zero.
- Positioning: *"Simple AI endurance coach. Connect Strava. Get answers."*
  Not "unified health platform". Specific beats broad on retention.

Every milestone below is filtered through "does this ship V1?". If no,
it's deferred to V2.

---

## ✅ What we have on the V1 critical path

### Infrastructure (live in production)
- Backend on Railway: `https://evovlerun-production.up.railway.app`
- Frontend on Vercel: `https://evovlerun.vercel.app`
- Supabase Postgres + Auth + RLS on every table
- 5 migrations applied (initial schema, mcp_api_keys, Garmin deep, metrics, oauth)
- Fernet-encrypted provider tokens
- HTTPS + CORS for claude.ai
- OAuth 2.1 + PKCE auth server (Dynamic Client Registration, /authorize, /token)
- Discovery metadata on root (RFC 9728) so Claude.ai connector "Connect" button works

### Strava integration (live, V1 core)
- OAuth flow: frontend → backend exchange → encrypted token storage
- Initial 90-day sync on first connect
- Webhook receiver for `create` / `update` / `delete` events
- Activity normalisation into our `workouts` schema
- Strava covers most data we need: distance, time, pace, HR (avg+max),
  cadence, power, elevation. Some splits.

### MCP chat surface (live, V1 core)
- 11 tools, kebab-case, Chirona-parity surface
- Hosted streamable-HTTP transport at `/mcp`
- Bearer + OAuth Bearer both accepted
- `conversation-initialisation-critical-instructions` — coaching guide
  that locks tone, response shape, plan-rendering grid format, and the
  ask-before-save rule
- `save-training-plan` is the only plan-write tool (single atomic call)
- Plan rendering format pinned: Mon-Sun grid with ISO week numbers,
  colored dots per session type

### Frontend (mostly done, needs V1 polish)
- Auth: login, signup, dashboard gating via middleware
- `/dashboard/mcp` — generate API keys, 3-tab installer (auto-install
  script / manual JSON / ChatGPT placeholder)
- `/dashboard/connections` — provider rows + sync controls
- `/dashboard/training` — active plan + plan-form
- `/oauth/consent` — Claude.ai approval screen
- Design tokens added: `bg-evr-warm` (#F5F0E8), `text-evr-accent` (#DC6B3F),
  `.evr-headline` serif

---

## 🟡 In progress (mid-flight, V1 critical)

1. **Marketing landing page** — convert `~/Downloads/evolverun/vercel.html`
   → Next.js route at `/`. Currently the root route is just a stub.
2. **Onboarding wizard** — convert `~/Downloads/evolverun/onboarding.jsx`
   → 5-question flow on `/onboarding`. Spec lives in
   `~/.claude/projects/-Users-valdemarstoerum/memory/chirona_pattern.md`.
   Adjust Q03 to show only Strava (no Garmin/Oura/etc. in V1).
3. **Graceful nulls for sleep/body tools** — `get-latest-sleep` and
   `get-latest-body` need to return "not available in Strava-only setup"
   messages instead of crashing or returning empty rows.

---

## ❌ What's missing for V1 ship

In priority order — tick top-down:

### Must-ship (blockers)
- [x] **Landing page** at `/` — Vercel-style hero, Strava-only positioning
- [~] ~~**Onboarding wizard** at `/onboarding`~~ — built, then rolled
      back because the answers didn't feed into anything actionable.
      Profile columns from migration 0006 still exist for V2; the route
      now just redirects to `/dashboard`. Re-enable when we wire the
      answers into `conversation-initialisation-critical-instructions`.
- [x] **Disable Garmin connector** in UI — card hidden from
      `/dashboard/connections`, `/dashboard/connections/garmin` redirects
- [x] **Replace dashboard root** with Vercel-style layout
      (tabs, stat row, today's plan, weekly load chart, recovery ring)
- [x] **Account page** at `/dashboard/account` — billing status pill,
      Start subscription / Manage billing buttons, logout
- [x] **Stripe Checkout integration** — single-tier subscription via
      `/billing/create-checkout-session`, webhook mirrors state onto profiles,
      paywall middleware gated by `NEXT_PUBLIC_ENFORCE_SUBSCRIPTION=true`
- [ ] **Apply Supabase migrations 0006 + 0007** — onboarding columns and
      Stripe billing columns on `profiles`
- [ ] **Configure Stripe in Railway** — create the V1 Product + Price in
      Stripe dashboard, set `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`,
      `STRIPE_WEBHOOK_SECRET` env vars, point Stripe webhook at
      `/billing/webhook`
- [ ] **Strava-only data handling** in MCP tools — null-safe paths for
      sleep, body composition, HR zones (Strava doesn't expose those)
- [ ] **Cookbook page** at `/dashboard/cookbook` — 10 baked prompts with
      Copy buttons (specs in chirona_pattern.md memory)
- [ ] **Brand decision** — keep "EvolveRun" or pick something simpler.
      Domain still `evolverun-production.up.railway.app` + `evovlerun.vercel.app`
      (typo in repo name). If renaming: also update Railway public domain,
      Vercel domain, Supabase project name, Stripe product name.

### Should-ship (high impact, not blocker)
- [ ] Email via Resend — welcome email, sync-completed email, weekly
      summary email (one per Monday morning)
- [ ] Privacy / Terms / Cookie pages — required for Stripe live mode
- [ ] Custom domain — `evolverun.com` or chosen brand. Probably worth
      buying before launching to first paying users.

### Nice-to-have (defer if needed)
- [ ] Shareable weekly summary — image render of the week's plan,
      Strava-style. Acquisition channel.
- [ ] Year-in-review PDF — once per user has 12+ months of data
- [ ] Marketing demo on landing page — convert VercelDemo from vercel-demo.jsx

---

## 🗄️ Deferred to V2+

These were built (some live, some scaffolded) but are NOT V1 surface:

- **Garmin official partner API** — apply when V1 has 10+ paying users to
  justify the effort
- **Oura, WHOOP, Polar OAuth** — add when users start asking for sleep/recovery
- **Terra aggregator** — only if MRR > $5k/mo and users are demanding
  Coros/Suunto/Wahoo native
- **Daily briefings** — explicitly rejected by founder ("for meget justering")
- **4-week reviews via Opus** — V2 feature; the LLM lives in the chat now
- **Limiter engine / metrics engine** — backend code still runs but not
  surfaced. Re-expose if users want it.
- **Plan generator (in-app)** — the chat assistant does this via
  `save-training-plan`. In-app form is a V2 convenience.
- **Performance model recompute on cron** — runs after sync today; can
  add scheduled cron when we have >100 users

---

## Strategic principles (carry-over from ChatGPT's advice)

1. **Sell "simple AI for Strava athletes"** — not "unified platform"
2. **Subscription from day 1** — no free tier. €9–14/mo or €29/quarter.
3. **Brand without "Strava" in the name** — but say "Works with Strava"
   liberally in copy. Reduces friction.
4. **Niche first** — pick one athlete archetype for the landing page
   copy. Best candidates given our data:
   - "AI coach for busy runners" (broad, easiest)
   - "Recovery intelligence for marathon training" (specific, premium)
   - "Training optimization from Strava data" (descriptive, low-energy)
5. **AI outputs must be actionable, not analytical**:
   - ✗ "Your VO2max is 56 ml/kg/min"
   - ✓ "You're likely under-recovered today — switch tomorrow's intervals
       to easy z2."
6. **Don't build platform features in V1** — integrations, dashboards,
   universal health graph all wait for V2.

## Differentiators worth keeping in mind (V2+)

From the original roadmap, still valid:
- Explainability Replay — click "why" on any session
- HRV-based overtraining prediction
- Race pace strategy AI (GPX + weather + pacing history)
- Hybrid philosophy engine (Daniels → Pfitzinger → Canova per phase)
- Voice journaling → Whisper → coach insight
- Injury Risk Score (ACWR + decoupling + sleep-debt)

None of these belong in V1. They're V2 hooks to keep customers retained
after 3 months.

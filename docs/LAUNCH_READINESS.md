# EvolveRun — Launch-Readiness Review

_Generated from a multi-agent adversarial audit (7 dimensions, 60 raw findings,
7 refuted as false alarms) plus a live visual pass and hand-verification of the
top blockers. Date: 2026-06-03._

**Verdict:** 🔴 **Not safe to launch yet.** The architecture is solid, but today
**any user who signs up gets the full paid product for free**, and a couple of
security/legal gaps would bite on day one. All are fixable in a focused day or two.

---

## Progress (branch `launch-prep`)

**Blockers**
| Blocker | State |
|---|---|
| #1 Subscription gating | ✅ code + tests · **ops:** set `ENFORCE_SUBSCRIPTION=true` in prod |
| #2 Strava webhook auth | ✅ code + tests · **ops:** re-register Strava callback URL with `?token=<secret>` |
| #3 Privacy/Terms pages | ✅ scaffolded at `/privacy` + `/terms` · **action:** fill the `[BRACKETED]` placeholders + have reviewed |

**High priority**
| Item | State |
|---|---|
| PKCE downgrade bypass | ✅ S256 mandatory; `plain` dropped; tests |
| `get_period_summary` crash | ✅ zero-distance guard; tests |
| Auth-code replay + refresh revocation | ✅ migration 0008 + single-use/reuse-detection + `/oauth/revoke`; **ops:** apply migration |
| Rate limiting | ✅ per-IP limits on register/token/webhook; tests |
| Password-reset flow | ✅ `/forgot-password` + `/reset-password`; **ops:** configure Supabase SMTP |
| Error monitoring (Sentry) | ✅ env-guarded init; **ops:** set `SENTRY_DSN` in prod |
| Hosted MCP onboarding copy | ✅ key install now uses `mcp-remote` (no clone) |

**All 7 high-priority items are now addressed.**

**Medium/polish** (branch `medium-polish`)
| Item | State |
|---|---|
| `replace_window` cross-plan delete | ✅ scoped to `plan_id` |
| Stripe webhook idempotency | ✅ event ledger (migration 0009); **ops:** apply migration |
| Client secret non-constant-time | ✅ `hmac.compare_digest` |
| `/oauth/deny` open redirect | ✅ backend validates `redirect_uri`; consent page has Cancel button |
| OG / Twitter / sitemap meta | ✅ full OpenGraph + `sitemap.ts` |
| Dashboard loaders swallow errors | ✅ throw on Supabase error |
| RLS — two `planned_workouts` reads miss `user_id` scope | remaining |
| `verify_aud: False` on access tokens | remaining (low risk — single resource server) |
| Strava brand assets ("Powered by Strava") | remaining |
| Contradictory copy ("Public Beta" vs. "no free tier") | remaining |

## 🚫 Launch blockers (fix before taking a single payment)

1. **MCP connector isn't gated on a subscription — free users get everything.**
   `backend/mcp_server/token_verifier.py:33` resolves any valid key/JWT to a user
   and returns `scopes=["mcp"]` with no subscription check; `backend/app/config.py:65`
   has `enforce_subscription = False` by default and even when on only guards
   `/dashboard` web pages, not the API that *is* the product.
   → Gate in `verify_token`: reject unless `profiles.subscription_status ∈ {active, trialing}`.
   _(Confirmed by direct read.)_

2. **Strava webhook is completely unauthenticated.**
   `backend/app/routers/providers.py:387` acts on attacker-controlled `owner_id`/
   `object_id` with no secret check; the `delete` branch hard-deletes from `workouts`.
   Strava athlete IDs are effectively public → forged delete events can wipe a
   user's synced workouts or force server-side fetches.
   → Require a secret token on the webhook URL; don't trust the body for deletes.
   _(Confirmed by direct read.)_

3. **No Privacy Policy / Terms pages.** No `/privacy` or `/terms` exist — a hard
   compliance gate for both Stripe (live-account standing) and Strava (API
   production approval requires a published privacy policy + data deletion).
   → Ship both pages + footer links.

## ⚠️ High priority (first week)

- **OAuth auth-code replay** — `jti` never persisted/checked, so a code is reusable
  within its 60s TTL (`oauth_jwt.py:72`, `oauth.py:258`). _(Confirmed.)_
- **PKCE downgrade-bypass** — enforcement is `if challenge:`; a code minted with an
  empty challenge skips PKCE; `plain` still advertised (`oauth.py:269`, `main.py:116`).
  → Require `S256` for all clients.
- **Refresh tokens can't be revoked** — stateless 30-day JWTs; rotation doesn't
  invalidate the prior token; no disconnect/revoke path (`oauth_jwt.py:156`).
- **`get_period_summary` ZeroDivisionError** when activities have null distance —
  crashes a core MCP tool (`period_summary.py:125`).
- **No error monitoring** (no Sentry/structured logging) — blind to failed webhooks/500s.
- **No rate limiting** on `/oauth/register`, `/billing/webhook`, `/oauth/token`, login.
- **No transactional email** — no password reset, no receipts/dunning.
- **MCP onboarding assumes a local repo clone** — `mcp_keys.py` hardcodes a
  server-side path + "clone the repo"; broken for hosted customers.

## 🔧 Medium / polish

- `save-training-plan` `replace_window` **deletes planned workouts across ALL of a
  user's plans**, not just the target (`plan_crud.py:245`) — data loss.
- Stripe webhook not idempotent / no event ledger; `past_due`/`unpaid` keep access.
- Backend uses the **service-role key (bypasses RLS)** → RLS is a backstop only;
  two `planned_workouts` reads scope by `plan_id` not `user_id` — tighten.
- Access-token `aud` check disabled; client secret is unsalted SHA-256 +
  non-constant-time compare.
- Consent screen shows attacker-controlled `client_name`; deny path is an open redirect.
- **Visual:** mobile nav links vanish with no menu; "Integrations" link mis-wired to
  `#how-it-works`; "Pricing" scrolls to the footer (no real pricing section);
  dashboard loaders swallow Supabase errors (silently show "empty").
- No OG/Twitter/sitemap meta — shared links render with no preview card.
- Missing Strava brand assets ("Powered by Strava" / "View on Strava") — required
  for Strava production approval.
- Dead code: 4 orphaned `_motion` components; footer GitHub link may 404;
  `DEPLOY.md` stale (MINIMAX vars, "20 tools"); "Public Beta"/"Start free trial"/
  "no free tier" copy is contradictory.

## ✅ Already solid

- Stripe done right where it counts: price server-side, webhook signature verified,
  secrets from env.
- Provider tokens Fernet-encrypted at rest.
- RLS present on every user-scoped table at the schema level.
- Stateless-JWT OAuth design is clean and scales; refresh tokens work end-to-end.
- The landing page itself is strong.

_Skeptic agents refuted 7 would-be findings as false alarms (e.g. "unbounded Strava
pagination" — bounded by the 90-day window; a claimed HRV date-truncation bias — math
checks out), so those are excluded above._

## Notes

- The adversarial verification pass completed 25 of 60 findings before its run was
  cut short, so the medium/low tier is "high-confidence but not all double-checked";
  blockers and most highs were confirmed by direct code reads.

# Changelog

All **notable** changes to EvolveRun, newest first — a founder-readable record of
what shipped and why. Format loosely follows
[Keep a Changelog](https://keepachangelog.com). EvolveRun is continuously deployed,
so entries are grouped by **date** rather than version tags.

Grouping per entry: **Added / Changed / Fixed / Ops**. This is for recall, not a
mirror of git history — see `CLAUDE.md` for what to log and what to skip.

## [Unreleased]

### Fixed
- Account page showed "€9 per month" while the actual price (and the rest of the
  site — pricing, landing, terms) is **€7.99**. Corrected the account-page copy.

## 2026-06-21

### Added
- Stripe billing wired up and live-tested in **test mode**: product + €9/mo EUR
  price, webhook (4 events) with signing secret in Railway, and a customer-portal
  configuration so the "View billing" button works.
- `CHANGELOG.md` + a CLAUDE.md rule to keep it current.

### Changed
- Account page: inline "Security" section replaced with a **Change password** button
  + modal (asks for the new password only).
- Dashboard and landing made **mobile-friendly** (Chirona-style tab bars; demo plays
  on scroll at full size; scroll-reveal box animations removed, button hovers kept).
- ChatGPT setup tab switched from an API-key form to the **MCP OAuth guide** (matches
  the Claude flow).

### Fixed
- **Stripe webhook** no longer leaves a paid subscription showing "No plan". Stripe
  delivers `subscription.created` (incomplete) and `.updated` (active) out of order;
  the handler now re-fetches the live subscription so the mirrored status can't
  regress. (`backend/app/routers/billing.py`)
- **ChatGPT MCP connect**: aligned the OAuth issuer trailing slash with FastMCP so
  ChatGPT's strict discovery validation passes.
- **Strava webhook**: removed the `?token=` query param from the callback URL (Strava
  rejects query params); events are ID-only and re-fetched via the authenticated API.

### Ops
- Strava webhook (re)registered as subscription `354010`.
- `ENFORCE_SUBSCRIPTION=false` during test-mode billing (test subs aren't real;
  turning the paywall on is part of go-live).

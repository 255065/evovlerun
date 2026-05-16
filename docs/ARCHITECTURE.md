# Arkitektur — EvolveRun

## High-level

```
┌──────────────┐        ┌──────────────────┐        ┌──────────────────┐
│  Brugerens   │        │   Next.js 15     │        │   FastAPI        │
│  browser     │◄──────►│   (Vercel)       │◄──────►│   (Render/Fly)   │
└──────────────┘        │   Auth, UI,      │        │   AI orchestr.,  │
                        │   Server Actions │        │   sync workers   │
                        └────────┬─────────┘        └────┬─────────────┘
                                 │                       │
                                 ▼                       ▼
                            ┌─────────────────────────────────┐
                            │       Supabase (Postgres)       │
                            │  Auth · RLS · Storage · Edge Fn │
                            └─────────────┬───────────────────┘
                                          │
                          ┌───────────────┼─────────────────┐
                          ▼               ▼                 ▼
                     ┌────────┐      ┌────────┐        ┌────────┐
                     │ Garmin │      │ Strava │  ...   │  Oura  │
                     └────────┘      └────────┘        └────────┘
```

## Hvor lever hvad

### Frontend (Next.js 15, App Router)
- **Auth-flows** (login, signup, OAuth-callback) via Supabase SSR.
- **Dashboard + UI** (Server Components læser direkte fra Supabase).
- **Server Actions** håndterer formularer (login, signup, log ud).
- **Middleware** opfriskerer sessionen og redirecter ulogged-in fra `/dashboard`.

### Backend (FastAPI, Python 3.13)
- **AI orchestration**: kald til Claude (Sonnet/Opus/Haiku) — for tungt at gøre fra frontend.
- **Wearable sync workers**: trækker data fra Garmin/Strava/etc. og normaliserer til `workouts` + `daily_metrics`.
- **Webhooks** fra providers (push fra Strava etc.).
- **Schedulers** (cron-jobs): daglige briefings, 4-ugers reviews.

Backend læser/skriver til Supabase med `service_role`-nøglen og omgår RLS bevidst, fordi den agerer *på vegne af* brugeren i baggrunden.

### Database (Supabase Postgres)
- Alle tabeller har RLS — frontend kan kun se egen data direkte.
- Backend bruger `service_role` til writes der kommer fra cron/sync workers.

## Datafluxen for ét workout

1. Bruger løber en tur. Garmin uploader til Garmin Connect.
2. Garmin sender webhook → `POST /ingest/webhook/garmin` på FastAPI.
3. FastAPI verificerer signaturen, finder bruger via `oauth_connections`, henter aktivitetsdata via Garmin API.
4. Backend normaliserer → insert i `workouts`.
5. Backend opdaterer `performance_profiles` (CTL/ATL/TSB/ACWR) hvis dagen er ny.
6. Hvis det er aften, trigger backend `coach_briefings` med post-workout-analyse via Claude.
7. Frontend Server Component læser nye rows og viser dem på dashboardet.

## AI-laget

| Brug | Model | Hvorfor |
|---|---|---|
| Dagligt briefing, simple klassifikationer | Haiku 4.5 | Billigt, hurtigt, godt nok til let reasoning |
| Plan-adapter, post-workout-analyse, race strategy | Sonnet 4.6 | Default workhorse — god balance |
| Limiter detection, 4-ugers review, performance forecasting | Opus 4.7 | Tung analyse over megen kontekst |
| Sports-science RAG (Daniels, Hansons, Pfitzinger osv.) | Embeddings | Lookup ind i en knowledge base, ikke generativ |

**Tool calling** bruges når Claude har brug for at slå op i brugerens historik (workouts, metrics, plans). Defineret som FastAPI-tools som modellen kan kalde.

**Prompt caching** bruges til faste system prompts (filosofi-engine, athlete profile) for at spare 60-90% i cost på gentagne kald.

## Sikkerhed

- OAuth-tokens krypteret med Fernet før insert (`TOKEN_ENCRYPTION_KEY`).
- RLS på alle tabeller — den eneste vej rundt er service-role som kun lever på backend.
- Backend verificerer Supabase JWTs via HS256 + `SUPABASE_JWT_SECRET`.
- Service-role-nøglen er **kun** i backend `.env`, aldrig i frontend.
- CORS låst til kendte origins via `CORS_ORIGINS`.

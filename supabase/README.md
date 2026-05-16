# Supabase

Database schema for EvolveRun.

## Anvendelse

1. Opret et nyt projekt på https://supabase.com
2. Gå til **SQL Editor → New query**
3. Kopiér indholdet af `migrations/0001_initial_schema.sql` ind og kør
4. Hent dine nøgler fra **Settings → API**:
   - `Project URL` → `NEXT_PUBLIC_SUPABASE_URL` + `SUPABASE_URL`
   - `anon public` → `NEXT_PUBLIC_SUPABASE_ANON_KEY` + `SUPABASE_ANON_KEY`
   - `service_role` (server-only!) → `SUPABASE_SERVICE_ROLE_KEY`
   - **Settings → API → JWT Settings → JWT Secret** → `SUPABASE_JWT_SECRET`

## Tabeller

| Tabel | Formål |
|---|---|
| `profiles` | Bruger-profil (alder, vægt, HR, foretrukken filosofi) |
| `oauth_connections` | Krypterede tokens til Garmin/Strava/Oura/Whoop |
| `workouts` | Hver aktivitet (run, ride, swim, strength) |
| `daily_metrics` | Daglig wellness (sleep, HRV, readiness) |
| `performance_profiles` | Longitudinel fysiologisk snapshot (VO2max, threshold, CTL/ATL/TSB, ACWR) |
| `limiter_history` | AI-detekterede limiters over tid med begrundelse |
| `training_plans` | Genererede periodiserede planer |
| `planned_workouts` | Individuelle sessioner inde i en plan, inkl. *rationale* (hvorfor) |
| `coach_briefings` | Proaktive AI-beskeder (dagligt / ugentligt / post-workout) |

## Sikkerhed

- **RLS** er enabled på alle tabeller — brugere kan kun se deres egen data.
- Backend bruger `service_role`-nøglen til at omgå RLS når det er nødvendigt (fx for cron jobs).
- OAuth-tokens er **Fernet-krypteret** i appen før insert. Selv hvis nogen får database-adgang, kan tokens ikke bruges uden `TOKEN_ENCRYPTION_KEY`.

## Næste migrationer

Tilføj nye `.sql`-filer i `migrations/` med inkrementerende prefix (`0002_...`, `0003_...`).

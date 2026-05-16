# Roadmap

## Hvor vi er (v0.1.0 — scaffold)
- ✅ Monorepo med frontend + backend + supabase + docs
- ✅ Next.js 15: landing, login/signup, beskyttet dashboard, navigation
- ✅ FastAPI: health, auth/me, ingestion-stubs, training-stubs
- ✅ Supabase: 9 tabeller med RLS + auto-profile-trigger
- ✅ Krypteret token-opbevaring klar (Fernet)
- ✅ Type-check + tests grønne

## Næste skridt — milestones

### M1: Få det til at virke end-to-end lokalt (1–2 dage)
- [ ] Opret rigtigt Supabase-projekt og kør migrationen
- [ ] Udfyld `.env`-filer i frontend og backend
- [ ] Signup → login → se dashboard
- [ ] Verificér at `/auth/me` på backend returnerer brugeren med Supabase-JWT

### M2: Første rigtige integration — Strava (3–5 dage)
Strava er nemmest. Garmin kræver partneraftale.
- [ ] Strava OAuth-flow (frontend redirect → backend exchange code → token gemmes krypteret)
- [ ] Initial sync (sidste 90 dages aktiviteter → `workouts`)
- [ ] Webhook-modtager (Strava-events: create / update / delete)
- [ ] Dashboard viser sidste 10 aktiviteter

### M3: Performance Model + ACWR (3–5 dage)
- [ ] Beregn TRIMP / TSS per workout (Banister / Coggan)
- [ ] Dagligt cron-job opdaterer `performance_profiles` (CTL/ATL/TSB/ACWR)
- [ ] Dashboard viser CTL-graf og ACWR-zone (under 0.8 = detraining, 0.8–1.3 = optimal, >1.5 = farligt)

### M4: Daily Briefing (Claude) (2–3 dage)
- [ ] System prompt med atletens profil + seneste 14 dages data
- [ ] Haiku genererer kort dagligt briefing om morgenen
- [ ] Tool-call: `get_planned_workout(date)`, `get_recent_workouts(days)`, `get_readiness()`
- [ ] Briefing viser **hvorfor** ved at citere data-punkter

### M5: Limiter Detection + 4-week Review (5–7 dage)
- [ ] Opus 4.7 kører hver 28. dag på fuld træningshistorik
- [ ] Output: primær limiter + sekundær + confidence + structured reasoning → `limiter_history`
- [ ] Hvis primær limiter ændrer sig, foreslås plan-adaptation

### M6: Training Plan Generator (7–10 dage)
- [ ] Plan-builder UI: race-type, mål-tid, race-dato, filosofi
- [ ] Sonnet bygger 12–20-ugers periodiseret plan med daglige sessioner
- [ ] Plan gemmes i `training_plans` + alle sessions i `planned_workouts`
- [ ] Daglig "dynamic adapter": justér i morgen baseret på i dag (readiness, missed session, fatigue)

### M7: Multi-provider sync (Oura, Whoop, Garmin) (5–7 dage)
- [ ] Generisk provider-interface i backend
- [ ] OAuth-flows + token-refresh for hver
- [ ] `daily_metrics` unifies sleep/HRV/readiness fra hver provider

### M8: Billing + Polish (3–5 dage)
- [ ] Stripe subscription (3 tiers: Free / Pro / Elite)
- [ ] Resend til transactional emails (briefings, alerts)
- [ ] Onboarding-flow
- [ ] Empty-states og fejl-håndtering

## Feature-idéer der differentierer fra Chirona

(Mine forslag — vi vælger sammen hvilke der kommer i hvilken milestone.)

### 1. Explainability Replay
Når coach foreslår "kør 8x400m i 3:30/km", kan brugeren klikke "vis mig hvorfor" og få:
- Citat fra training philosophy (Daniels: VO2max-intervaller skal være 3:30–5min)
- De seneste 3 ugers data der trigger sessionen (CTL +12%, threshold-pace forbedret 4s/km)
- "Hvis du ikke føler dig klar, klik her" → coach justerer i realtid med begrundelse

### 2. Physiological Digital Twin
Vedligehold en "fysiologisk model" af brugeren der opdateres efter hver session:
- Estimeret VO2max-trajektorie (ikke bare seneste tal)
- Confidence intervals: "din threshold-pace er 3:55 ± 4s"
- Forecast: "ved nuværende trend rammer du sub-3:30 marathon med 67% sandsynlighed"

### 3. HRV-baseret overtræning-prediction
HRV alene er støjende, men 7-dages glidende baseline der dropper >5% i 5+ dage er en stærk overtrænings-signal. Coach fanger det *før* brugeren føler det — sender alert med specifik anbefaling (deload, ikke just "easy day").

### 4. Race Pace Strategy AI (med terrain + vejr)
- Træk race-rute fra GPX
- Træk vejrprognose for race-dagen
- Generer pacing-plan per kilometer baseret på elevation, vind, temperatur og brugerens specifikke pacing-historie (positive/negative split-tendency)

### 5. Hybrid Philosophy Engine
I stedet for "vælg én filosofi", lad coach vælge per fase:
- Base = polariseret (Norwegian-style threshold) til at bygge aerob
- Build = Pfitzinger (LT-fokuseret)
- Peak = Canova (race-specifik long runs)
- Taper = Hansons (kort, høj intensitet)

Med eksplicit begrundelse for hvert valg.

### 6. Voice journaling → indsigt
Brugeren optager 30s voice memo efter sin tur ("benene tunge, men luft fin"). Whisper transkriberer, Haiku ekstraherer signal ("muscular fatigue, cardio OK"). Bygger en *subjective* tidslinje at korrelere med objektiv data — særligt værdifuldt for at fange tidlige skader.

### 7. Form Analyzer (slow-mo video)
Bruger uploader 10s video af sit løb fra siden. Claude Vision + MediaPipe/PoseNet extracterer:
- Cadence
- Foot strike pattern
- Heel kick / knee drive
- Trunk lean
Sammenligner med elite-baselines og foreslår specifikke drills.

### 8. Community-baseret benchmarking (anonymized)
"Brugere med din profil (35yo, 70kg, 3:30 marathon-mål, 60km/uge) bruger gennemsnitligt 6 uger på base-fasen — du er 2 uger inde." Giver kontekst uden at sammenligne med urealistiske elites.

### 9. Coach Personality Selector
- "Maria" — empatisk, fokus på balance og mental sundhed
- "Marius" — direkte, no-nonsense, Norwegian-style
- "Pheidippides" — klassisk, refererer til træningshistorie
Brugeren vælger ved onboarding. Briefing-tonen ændres.

### 10. Injury Risk Score
Kombinerer: ACWR, cadence-decay i lange ture, cardiac drift, sleep-debt, biomekanik fra Form Analyzer. Score 0–100 daglig. Når den passerer tærskel, automatisk deload-forslag.

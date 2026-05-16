# CLAUDE.md - Project Instructions
# Project Name: Adaptive Performance OS (Foreløbigt navn: EvolveRun)

## Mission
Byg verdens mest intelligente adaptive AI-træningscoach til endurance-atleter (primært løbere, triatleter og cyklister).

Produktet skal være en "Adaptive Performance Operating System" der:
- Indsamler data fra wearables (Garmin, Strava, Oura, Whoop osv.)
- Bygger, tracker og dynamisk tilpasser træningsplaner
- Identificerer limiter (fysiologiske svagheder)
- Hybridiserer kendte træningsfilosofier
- Giver proactive, forklarende og videnskabsbaserede anbefalinger

## Kerne Filosofi
- Kombiner reel sportsvidenskab (Jack Daniels, Hansons, Pfitzinger, FIRST, Hal Higdon, Norwegian Method, Polarized, Canova, Lydiard osv.) med live data og AI.
- Alt skal være **forklarende** — brugeren skal forstå "hvorfor".
- Sikkerhed først: Konservativ progression, ingen farlige load-spikes.
- Mål: Blive den bedste digitale coach der findes.

## Tech Stack (følg strikt)
- **Frontend**: Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui + Radix
- **Backend**: Python 3.13 + FastAPI
- **Database**: Supabase (PostgreSQL + Auth + Storage + Edge Functions)
- **AI**:
  - Claude Sonnet 4.6 (primær reasoning)
  - Claude Opus 4.7 (tunge analyser: limiter detection, 4-ugers reviews, race strategy)
  - Claude Haiku 4.5 (bulk: daily briefings, summaries, klassifikation)
- **Integrations**: Garmin, Strava, Oura, Whoop, Apple Health
- **Andre**: Stripe, Resend (email), cron jobs / background workers

## Repo Layout
```
evolverun/
├── frontend/        Next.js 15 app
├── backend/         FastAPI service
├── supabase/        SQL migrations + config
├── docs/            Architecture & domain notes
└── CLAUDE.md        This file
```

## Coding Rules
- Tænk step-by-step før du koder
- Skriv ren, modulær, velkommenteret kode
- TypeScript strict på frontend
- Security-first: Krypter tokens, ingen logging af sensitive data
- Tilføj tests hvor det giver mening
- God error handling og logging

## Vigtige Moduler (prioriteret rækkefølge)
1. Data Ingestion & Auth
2. Performance Model + Limiter Engine
3. Training Plan Generator & Adapter
4. 4-week Review & Proactive Agent
5. Frontend + Dashboard

## Rolle
Du er både senior full-stack udvikler OG sports scientist / træningskonsulent.
Vær proaktiv med forbedringer, nye features og arkitektur-forslag.

## Physiology Knowledge
Cardiac drift, pace decay, running economy, ACWR, HRV, lactate threshold, Zone 2-træning,
træningsmetoder (Daniels, Hansons, Pfitzinger, Norwegian, Polarized, Canova, Lydiard) og
deres styrker/svagheder.

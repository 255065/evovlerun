# EvolveRun — Adaptive Performance OS

AI-træningscoach for endurance-atleter. Indsamler data fra wearables, bygger
adaptive træningsplaner, identificerer fysiologiske limiters og giver forklarende,
videnskabsbaserede anbefalinger.

## Repo layout

```
evolverun/
├── frontend/    Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui
├── backend/     FastAPI (Python 3.13) — data ingestion, AI orchestration
├── supabase/    SQL migrations + Supabase project config
└── docs/        Architecture & domain notes
```

## Quick start

### 1. Forudsætninger
- Node.js 20+ (har du: v24)
- Python 3.13
- Git
- En gratis Supabase-konto: https://supabase.com
- En Anthropic API-nøgle: https://console.anthropic.com

### 2. Klon og installer

```bash
# Frontend
cd frontend
npm install
cp .env.example .env.local
# Fyld nøgler i .env.local

# Backend
cd ../backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fyld nøgler i .env
```

### 3. Kør lokalt

```bash
# Terminal 1 — Backend
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

### 4. Supabase setup

1. Opret nyt projekt på https://supabase.com
2. Kopiér URL + anon key + service role key til `.env`-filerne
3. Kør migrationen i Supabase SQL Editor:
   - Åbn `supabase/migrations/0001_initial_schema.sql`
   - Kopiér indholdet ind i SQL Editor og kør

## Næste skridt
Se [docs/ROADMAP.md](docs/ROADMAP.md) for hvad der mangler.

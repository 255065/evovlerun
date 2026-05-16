-- ============================================================================
-- EvolveRun — Initial schema
-- Run this in the Supabase SQL Editor (Project → SQL Editor → New query).
-- All tables are scoped per-user with Row-Level Security (RLS).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Extensions
-- ----------------------------------------------------------------------------
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ----------------------------------------------------------------------------
-- Helper: auto-update updated_at on row changes
-- ----------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ============================================================================
-- profiles — extends auth.users with sport-specific attributes
-- ============================================================================
create table if not exists public.profiles (
  id              uuid primary key references auth.users(id) on delete cascade,
  email           text,
  full_name       text,
  date_of_birth   date,
  sex             text check (sex in ('male', 'female', 'other')),
  height_cm       numeric(5,2),
  weight_kg       numeric(5,2),
  primary_sport   text check (primary_sport in ('running', 'cycling', 'triathlon', 'swimming')) default 'running',
  experience_level text check (experience_level in ('beginner', 'intermediate', 'advanced', 'elite')),
  resting_hr      integer,
  max_hr          integer,
  preferred_units text check (preferred_units in ('metric', 'imperial')) default 'metric',
  timezone        text default 'UTC',
  preferred_philosophy text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create trigger profiles_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

-- Auto-create profile row when a user signs up.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, new.raw_user_meta_data->>'full_name')
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============================================================================
-- oauth_connections — encrypted wearable provider tokens
-- ============================================================================
create table if not exists public.oauth_connections (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  provider        text not null check (provider in ('garmin', 'strava', 'oura', 'whoop', 'apple_health')),
  provider_user_id text,
  -- Tokens are encrypted application-side before insert (Fernet).
  access_token_encrypted  text,
  refresh_token_encrypted text,
  scope           text,
  expires_at      timestamptz,
  last_sync_at    timestamptz,
  status          text check (status in ('active', 'expired', 'revoked', 'error')) default 'active',
  metadata        jsonb default '{}'::jsonb,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (user_id, provider)
);

create index if not exists oauth_connections_user_idx on public.oauth_connections(user_id);

create trigger oauth_connections_updated_at
  before update on public.oauth_connections
  for each row execute function public.set_updated_at();

-- ============================================================================
-- workouts — every recorded activity (run, ride, swim, gym, etc.)
-- ============================================================================
create table if not exists public.workouts (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  source          text not null check (source in ('garmin', 'strava', 'oura', 'whoop', 'apple_health', 'manual')),
  source_id       text,
  sport           text not null check (sport in ('running', 'cycling', 'swimming', 'strength', 'walking', 'hiking', 'other')),
  started_at      timestamptz not null,
  duration_seconds integer not null,
  distance_m      numeric(10,2),
  elevation_gain_m numeric(8,2),
  avg_hr          integer,
  max_hr          integer,
  avg_pace_s_per_km numeric(7,2),
  avg_power_w     numeric(7,2),
  normalized_power_w numeric(7,2),
  trimp           numeric(7,2),       -- training impulse
  tss             numeric(7,2),       -- training stress score
  perceived_effort smallint check (perceived_effort between 1 and 10),
  notes           text,
  raw_payload     jsonb,
  created_at      timestamptz not null default now(),
  unique (user_id, source, source_id)
);

create index if not exists workouts_user_started_idx on public.workouts(user_id, started_at desc);
create index if not exists workouts_user_sport_idx on public.workouts(user_id, sport);

-- ============================================================================
-- daily_metrics — daily wellness snapshot (sleep, HRV, readiness)
-- ============================================================================
create table if not exists public.daily_metrics (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  metric_date     date not null,
  resting_hr      integer,
  hrv_rmssd       numeric(6,2),
  sleep_minutes   integer,
  sleep_score     smallint,
  readiness_score smallint,
  body_battery    smallint,
  weight_kg       numeric(5,2),
  body_temp_delta numeric(4,2),
  raw_payload     jsonb,
  created_at      timestamptz not null default now(),
  unique (user_id, metric_date)
);

create index if not exists daily_metrics_user_date_idx on public.daily_metrics(user_id, metric_date desc);

-- ============================================================================
-- performance_profiles — longitudinal physiological model snapshots
-- ============================================================================
create table if not exists public.performance_profiles (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  snapshot_date   date not null default current_date,
  vo2max_estimated numeric(5,2),
  lactate_threshold_hr integer,
  lactate_threshold_pace_s_per_km numeric(7,2),
  critical_power_w numeric(7,2),
  running_economy numeric(6,2),
  fitness_ctl     numeric(7,2),      -- chronic training load (42-day)
  fatigue_atl     numeric(7,2),      -- acute training load (7-day)
  form_tsb        numeric(7,2),      -- training stress balance (CTL - ATL)
  acwr            numeric(5,3),      -- acute:chronic workload ratio
  notes           jsonb default '{}'::jsonb,
  created_at      timestamptz not null default now(),
  unique (user_id, snapshot_date)
);

create index if not exists performance_profiles_user_date_idx
  on public.performance_profiles(user_id, snapshot_date desc);

-- ============================================================================
-- limiter_history — AI-detected physiological limiters over time
-- ============================================================================
create table if not exists public.limiter_history (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  detected_at     timestamptz not null default now(),
  primary_limiter text not null check (primary_limiter in (
    'aerobic_capacity', 'running_economy', 'muscular_endurance',
    'lactate_threshold', 'anaerobic_capacity', 'recovery', 'neuromuscular'
  )),
  secondary_limiter text,
  confidence      numeric(3,2) check (confidence between 0 and 1),
  evidence        jsonb,             -- structured reasoning from Claude
  recommended_focus text,
  created_at      timestamptz not null default now()
);

create index if not exists limiter_history_user_idx on public.limiter_history(user_id, detected_at desc);

-- ============================================================================
-- training_plans — generated periodized plans
-- ============================================================================
create table if not exists public.training_plans (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  status          text not null check (status in ('active', 'completed', 'abandoned', 'paused')) default 'active',
  race_type       text not null check (race_type in ('5k', '10k', 'half_marathon', 'marathon', 'ultra', 'triathlon', 'general_fitness')),
  race_date       date,
  target_time_seconds integer,
  philosophy      text not null check (philosophy in (
    'daniels', 'hansons', 'pfitzinger', 'norwegian', 'polarized', 'lydiard', 'auto_hybrid'
  )),
  start_date      date not null,
  weeks           integer not null,
  current_phase   text check (current_phase in ('base', 'build', 'peak', 'taper', 'race', 'recovery')),
  plan_json       jsonb not null,    -- full structured plan
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists training_plans_user_status_idx on public.training_plans(user_id, status);

create trigger training_plans_updated_at
  before update on public.training_plans
  for each row execute function public.set_updated_at();

-- ============================================================================
-- planned_workouts — individual sessions inside a plan
-- ============================================================================
create table if not exists public.planned_workouts (
  id              uuid primary key default uuid_generate_v4(),
  plan_id         uuid not null references public.training_plans(id) on delete cascade,
  user_id         uuid not null references public.profiles(id) on delete cascade,
  scheduled_date  date not null,
  session_type    text not null,    -- easy, tempo, intervals, long, recovery, race, strength
  sport           text not null default 'running',
  duration_min    integer,
  distance_m      numeric(10,2),
  description     text,
  intensity_zones jsonb,            -- target HR/pace zones
  rationale       text,             -- WHY this session (explainability)
  completed_workout_id uuid references public.workouts(id) on delete set null,
  status          text check (status in ('scheduled', 'completed', 'skipped', 'modified')) default 'scheduled',
  ai_adjustments  jsonb default '[]'::jsonb,   -- log of dynamic adjustments
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists planned_workouts_user_date_idx
  on public.planned_workouts(user_id, scheduled_date);

create trigger planned_workouts_updated_at
  before update on public.planned_workouts
  for each row execute function public.set_updated_at();

-- ============================================================================
-- coach_briefings — proactive daily / weekly messages from the AI coach
-- ============================================================================
create table if not exists public.coach_briefings (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  briefing_type   text not null check (briefing_type in (
    'daily', 'weekly', 'post_workout', 'post_race', '4_week_review', 'alert'
  )),
  for_date        date not null default current_date,
  summary         text not null,
  body            text not null,
  reasoning       jsonb,            -- structured "why" — links to data points
  model_used      text,
  read_at         timestamptz,
  created_at      timestamptz not null default now()
);

create index if not exists coach_briefings_user_date_idx
  on public.coach_briefings(user_id, for_date desc);

-- ============================================================================
-- Row Level Security
-- Everyone gets their own data — service-role key bypasses these.
-- ============================================================================
alter table public.profiles            enable row level security;
alter table public.oauth_connections   enable row level security;
alter table public.workouts            enable row level security;
alter table public.daily_metrics       enable row level security;
alter table public.performance_profiles enable row level security;
alter table public.limiter_history     enable row level security;
alter table public.training_plans      enable row level security;
alter table public.planned_workouts    enable row level security;
alter table public.coach_briefings     enable row level security;

-- profiles: users can read/update their own row only.
create policy "profile is self-readable" on public.profiles
  for select using (auth.uid() = id);
create policy "profile is self-updatable" on public.profiles
  for update using (auth.uid() = id);

-- Generic owner-only policy for the remaining tables.
do $$
declare
  t text;
begin
  for t in select unnest(array[
    'oauth_connections', 'workouts', 'daily_metrics', 'performance_profiles',
    'limiter_history', 'training_plans', 'planned_workouts', 'coach_briefings'
  ]) loop
    execute format('create policy "%I owner read" on public.%I for select using (auth.uid() = user_id);', t, t);
    execute format('create policy "%I owner insert" on public.%I for insert with check (auth.uid() = user_id);', t, t);
    execute format('create policy "%I owner update" on public.%I for update using (auth.uid() = user_id);', t, t);
    execute format('create policy "%I owner delete" on public.%I for delete using (auth.uid() = user_id);', t, t);
  end loop;
end$$;

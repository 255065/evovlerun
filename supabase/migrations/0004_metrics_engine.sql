-- ============================================================================
-- EvolveRun — Metrics Engine + Post-workout AI
--
-- Adds:
--   • Per-snapshot computed metrics (VO2max via VDOT, threshold pace/HR,
--     running economy proxy, fatigue resistance, recovery capacity)
--   • Indices for trend queries across 4/8/12-week windows
--   • Per-workout AI analysis cache (coach_briefings.briefing_type = post_workout)
--
-- Re-runnable.
-- ============================================================================

alter table public.performance_profiles
  add column if not exists vdot                            numeric(5,2),
  add column if not exists vo2max_evolverun                numeric(5,2),
  add column if not exists threshold_pace_s_per_km_evolverun numeric(7,2),
  add column if not exists threshold_hr_evolverun          integer,
  -- Running economy proxy = sec/km per bpm at z2 efforts. Lower = better.
  add column if not exists running_economy_s_per_km_per_bpm numeric(6,3),
  -- 0-100 score: higher = more fatigue-resistant (lower decoupling on long runs).
  add column if not exists fatigue_resistance_score        numeric(5,2),
  -- 0-100 score: higher = recovers faster from high-load weeks.
  add column if not exists recovery_capacity_score         numeric(5,2),
  -- Samples used to compute the above (transparency / debug).
  add column if not exists metrics_inputs                  jsonb;

-- Index for fast "metric over time" queries — already exists on user+date but
-- explicit date-desc helps trend windows.
create index if not exists performance_profiles_user_date_desc_idx
  on public.performance_profiles(user_id, snapshot_date desc);

-- Link post-workout briefings to the activity they analyzed so we don't
-- re-analyze the same workout twice and so the UI can pull "the analysis for
-- this workout" cheaply.
alter table public.coach_briefings
  add column if not exists workout_id  uuid references public.workouts(id) on delete cascade,
  add column if not exists analysis_inputs jsonb;

create index if not exists coach_briefings_workout_idx
  on public.coach_briefings(workout_id) where workout_id is not null;

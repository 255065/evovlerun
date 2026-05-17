-- ============================================================================
-- EvolveRun — Garmin deep-data expansion
--
-- Adds room for everything we now pull from Garmin Connect beyond basic
-- activity metadata: HR/power zones, splits, weather, daily stress/SpO2/
-- respiration/steps, and Garmin's own performance estimates (VO2max, LT,
-- training status, race predictions, endurance/hill/fitness-age scores).
--
-- Designed to be additive — no destructive changes. Re-runs are safe.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- workouts — per-activity richer fields
-- ----------------------------------------------------------------------------
alter table public.workouts
  add column if not exists cadence_avg          integer,
  add column if not exists cadence_max          integer,
  add column if not exists temperature_c        numeric(4,1),
  add column if not exists calories             integer,
  add column if not exists aerobic_te           numeric(3,1),       -- Garmin 0–5
  add column if not exists anaerobic_te         numeric(3,1),       -- Garmin 0–5
  add column if not exists training_load        numeric(8,2),       -- Garmin EPOC-based
  add column if not exists hr_zone_seconds      jsonb,              -- {z1:300,z2:..,...}
  add column if not exists power_zone_seconds   jsonb,
  add column if not exists cardiac_drift_pct    numeric(5,2),
  add column if not exists pace_decay_pct       numeric(5,2),
  add column if not exists polarized_score      numeric(4,2),       -- pyrenees/sub-95 etc.
  add column if not exists weather_payload      jsonb,              -- temp+humidity+wind
  add column if not exists vo2max_at_activity   numeric(5,2);       -- Garmin vo2max stamp

-- ----------------------------------------------------------------------------
-- workout_splits — laps with per-split HR/pace/cadence/power
-- ----------------------------------------------------------------------------
create table if not exists public.workout_splits (
  id              uuid primary key default uuid_generate_v4(),
  workout_id      uuid not null references public.workouts(id) on delete cascade,
  user_id         uuid not null references public.profiles(id) on delete cascade,
  split_index     integer not null,                 -- 1-based lap number
  split_type      text,                             -- 'lap', 'manual', 'rest_recovery', 'climb'
  duration_s      integer,
  distance_m      numeric(10,2),
  avg_hr          integer,
  max_hr          integer,
  avg_pace_s_per_km numeric(7,2),
  avg_speed_mps   numeric(6,3),
  avg_cadence     integer,
  avg_power_w     numeric(7,2),
  elevation_gain_m numeric(8,2),
  intensity       text,                             -- recovery/easy/threshold/...
  created_at      timestamptz not null default now(),
  unique (workout_id, split_index)
);

create index if not exists workout_splits_workout_idx on public.workout_splits(workout_id);
create index if not exists workout_splits_user_idx on public.workout_splits(user_id);

-- ----------------------------------------------------------------------------
-- daily_metrics — recovery deep-dive (stress, SpO2, respiration, activity)
-- ----------------------------------------------------------------------------
alter table public.daily_metrics
  add column if not exists stress_avg                  smallint,
  add column if not exists stress_max                  smallint,
  add column if not exists steps                       integer,
  add column if not exists floors_climbed              integer,
  add column if not exists intensity_minutes_moderate  integer,
  add column if not exists intensity_minutes_vigorous  integer,
  add column if not exists spo2_avg                    smallint,
  add column if not exists spo2_min                    smallint,
  add column if not exists respiration_avg             smallint,
  add column if not exists respiration_min             smallint,
  add column if not exists respiration_max             smallint,
  add column if not exists body_fat_pct                numeric(4,1),
  add column if not exists active_calories             integer,
  add column if not exists total_calories              integer;

-- ----------------------------------------------------------------------------
-- performance_profiles — bundle Garmin's own estimates with our derived metrics
-- ----------------------------------------------------------------------------
alter table public.performance_profiles
  add column if not exists garmin_training_status     text,            -- productive/peaking/...
  add column if not exists garmin_training_load_focus text,            -- aerobic/anaerobic/...
  add column if not exists garmin_endurance_score     integer,
  add column if not exists garmin_hill_score          integer,
  add column if not exists garmin_fitness_age         integer,
  add column if not exists garmin_running_tolerance   integer,
  add column if not exists garmin_vo2max              numeric(5,2),    -- separate from our own estimate
  add column if not exists garmin_lt_hr               integer,
  add column if not exists garmin_lt_pace_s_per_km    numeric(7,2),
  add column if not exists race_prediction_5k_s       integer,
  add column if not exists race_prediction_10k_s      integer,
  add column if not exists race_prediction_hm_s       integer,
  add column if not exists race_prediction_marathon_s integer,
  add column if not exists body_fat_pct               numeric(4,1),
  add column if not exists muscle_mass_kg             numeric(5,2),
  add column if not exists ftp_w                      numeric(6,2);    -- cycling FTP

-- ----------------------------------------------------------------------------
-- personal_records — Garmin / provider-tracked best efforts
-- ----------------------------------------------------------------------------
create table if not exists public.personal_records (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  source          text not null check (source in ('garmin', 'strava', 'manual')),
  record_type     text not null,            -- best_5k_s, best_10k_s, longest_run_m, biggest_climb_m, ...
  value           numeric(12,3) not null,   -- seconds, meters, etc. (unit lives in record_type)
  unit            text,                     -- 's', 'm', 'kg', 'w' — descriptive only
  achieved_at     timestamptz,
  activity_source_id text,                  -- provider's activity id if linked
  raw_payload     jsonb,
  created_at      timestamptz not null default now(),
  unique (user_id, source, record_type, achieved_at)
);

create index if not exists personal_records_user_idx on public.personal_records(user_id, achieved_at desc);

-- ----------------------------------------------------------------------------
-- RLS for new tables
-- ----------------------------------------------------------------------------
alter table public.workout_splits enable row level security;
alter table public.personal_records enable row level security;

do $$
declare t text;
begin
  for t in select unnest(array['workout_splits', 'personal_records']) loop
    execute format('drop policy if exists "%I owner read" on public.%I;', t, t);
    execute format('drop policy if exists "%I owner insert" on public.%I;', t, t);
    execute format('drop policy if exists "%I owner update" on public.%I;', t, t);
    execute format('drop policy if exists "%I owner delete" on public.%I;', t, t);
    execute format('create policy "%I owner read"   on public.%I for select using (auth.uid() = user_id);', t, t);
    execute format('create policy "%I owner insert" on public.%I for insert with check (auth.uid() = user_id);', t, t);
    execute format('create policy "%I owner update" on public.%I for update using (auth.uid() = user_id);', t, t);
    execute format('create policy "%I owner delete" on public.%I for delete using (auth.uid() = user_id);', t, t);
  end loop;
end$$;

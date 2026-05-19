-- ============================================================================
-- EvolveRun — V1 onboarding fields
--
-- Captures the answers to the 5-question wizard at /onboarding so the chat
-- assistant has user-supplied context (goal, weekly volume, preferred style)
-- without having to re-ask in every conversation. `onboarded_at` doubles as a
-- "has the user finished setup?" sentinel — null means we should send them
-- back to the wizard, non-null means they can land directly on the dashboard.
-- ============================================================================

alter table public.profiles
  add column if not exists onboarding_goal       text,
  add column if not exists onboarding_goal_detail jsonb,
  add column if not exists weekly_sessions       integer,
  add column if not exists weekly_hours          integer,
  add column if not exists training_style        text
    check (training_style in ('structured', 'freeflow', 'adaptive', 'hybrid')),
  add column if not exists preferred_ai_coach    text
    check (preferred_ai_coach in ('claude', 'gpt', 'gemini')),
  add column if not exists onboarded_at          timestamptz;

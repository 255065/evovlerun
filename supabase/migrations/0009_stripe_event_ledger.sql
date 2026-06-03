-- 0009_stripe_event_ledger.sql
-- Idempotency ledger for Stripe webhook events.
-- The webhook handler records each processed event id here before acting on it.
-- A UNIQUE constraint on event_id means a second delivery of the same event
-- causes a duplicate-key error, which the handler treats as "already processed"
-- and returns 200 without touching the DB again (Stripe expects 2xx on duplicates).

create table if not exists stripe_processed_events (
    event_id    text        primary key,   -- evt_... from Stripe
    event_type  text        not null,
    processed_at timestamptz not null default now()
);

-- Only the service-role key (backend) writes here.
alter table stripe_processed_events enable row level security;
-- No policies — service-role bypasses RLS.

-- Keep the table small: Stripe's retry window is 3 days.
-- A nightly cron (future) can prune rows older than 7 days.
-- For now just index by processed_at so a future cleanup is cheap.
create index if not exists stripe_processed_events_processed_at_idx
    on stripe_processed_events (processed_at);

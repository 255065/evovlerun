-- ============================================================================
-- EvolveRun — V1 billing (Stripe subscriptions)
--
-- We mirror just enough Stripe state on `profiles` to answer "is this user
-- allowed in the app right now?" without a roundtrip to Stripe on every
-- request. The source of truth is still Stripe; webhooks keep us in sync.
--
-- subscription_status values follow Stripe's vocabulary verbatim so we don't
-- have to translate: 'active' | 'trialing' | 'past_due' | 'canceled' |
-- 'incomplete' | 'incomplete_expired' | 'unpaid' | 'paused'.
-- ============================================================================

alter table public.profiles
  add column if not exists stripe_customer_id     text unique,
  add column if not exists stripe_subscription_id text unique,
  add column if not exists subscription_status    text,
  add column if not exists subscription_price_id  text,
  add column if not exists subscription_current_period_end timestamptz;

create index if not exists profiles_stripe_customer_idx
  on public.profiles(stripe_customer_id)
  where stripe_customer_id is not null;

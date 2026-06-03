-- ============================================================================
-- EvolveRun — OAuth token hardening
--
-- Our OAuth tokens are stateless JWTs, which means we cannot, on their own,
-- make an authorization code single-use or revoke a refresh token before it
-- expires. These two tiny tables add the minimum server-side state to do both:
--
--   oauth_consumed_tokens — records the jti of every redeemed auth code and
--     every rotated (spent) refresh token. A second presentation of the same
--     jti is a replay / refresh-token reuse and is rejected.
--
--   oauth_revoked_grants — a per-(user, client) revocation marker. Any access
--     or refresh token issued at/before revoked_at is treated as invalid, so a
--     "disconnect" or reuse-detection event kills the whole grant immediately.
--
-- Both are written only by the backend service-role key. RLS is enabled with
-- no policies, which denies all anon/authenticated access (service-role
-- bypasses RLS) — matching the posture of the other internal tables.
-- ============================================================================

create table if not exists public.oauth_consumed_tokens (
    jti         text primary key,
    typ         text not null,            -- 'auth_code' | 'refresh_token'
    user_id     uuid,
    client_id   text,
    consumed_at timestamptz not null default now()
);

-- Spent jtis can be pruned once they're past the token's max lifetime (auth
-- codes 60s, refresh tokens 30d). A scheduled job can safely:
--   delete from oauth_consumed_tokens where consumed_at < now() - interval '31 days';
create index if not exists oauth_consumed_tokens_consumed_at_idx
    on public.oauth_consumed_tokens(consumed_at);

create table if not exists public.oauth_revoked_grants (
    user_id    uuid not null,
    client_id  text not null,
    revoked_at timestamptz not null default now(),
    primary key (user_id, client_id)
);

alter table public.oauth_consumed_tokens enable row level security;
alter table public.oauth_revoked_grants  enable row level security;

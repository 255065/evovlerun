-- ============================================================================
-- EvolveRun — OAuth 2.1 server tables
--
-- Implements the auth-server side of Claude.ai's custom-connector flow:
--   1) Claude.ai POSTs /oauth/register → we issue a client_id (+ optional
--      secret) and record the redirect_uris it's allowed to call back to.
--   2) User is redirected to /oauth/authorize → frontend renders a consent
--      page → /oauth/approve issues a short-lived JWT authorization code.
--   3) Claude.ai POSTs /oauth/token with the code + PKCE verifier → we
--      validate and return a JWT access token.
--   4) Every MCP request carries that access token as a Bearer header.
--
-- Authorization codes and access tokens are JWTs (stateless, signed with
-- OAUTH_STATE_SECRET) so we don't need tables for them — they're verified by
-- signature alone. Clients DO need a table because they persist across
-- sessions.
-- ============================================================================

create table if not exists public.oauth_clients (
  id                 uuid primary key default uuid_generate_v4(),
  client_id          text not null unique,
  client_secret_hash text,                                     -- nullable for public clients
  client_name        text,
  redirect_uris      text[] not null,
  grant_types        text[] not null default array['authorization_code'],
  scopes             text[] not null default array['mcp'],
  is_public          boolean not null default true,            -- PKCE-only clients
  created_at         timestamptz not null default now(),
  last_used_at       timestamptz
);

create index if not exists oauth_clients_client_id_idx on public.oauth_clients(client_id);

-- We deliberately don't enable RLS here — OAuth clients aren't user-scoped.
-- They're application identities, not end-user resources. The backend reads
-- them with the service-role key and the frontend never touches the table.

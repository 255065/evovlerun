-- ============================================================================
-- MCP API keys
-- A user generates one of these and pastes it into Claude Desktop / ChatGPT
-- so the MCP server can identify them on every request.
-- ============================================================================

create table if not exists public.mcp_api_keys (
  id              uuid primary key default uuid_generate_v4(),
  user_id         uuid not null references public.profiles(id) on delete cascade,
  -- SHA-256 of the full key. We never store the raw key.
  key_hash        text not null,
  -- First 8 chars of the key shown in the UI so users can identify it.
  key_prefix      text not null,
  name            text not null,            -- user-supplied label, e.g. "MacBook Claude"
  scopes          text[] default array['read']::text[],
  last_used_at    timestamptz,
  revoked_at      timestamptz,
  created_at      timestamptz not null default now()
);

create index if not exists mcp_api_keys_user_idx     on public.mcp_api_keys(user_id);
create index if not exists mcp_api_keys_lookup_idx  on public.mcp_api_keys(key_hash) where revoked_at is null;

alter table public.mcp_api_keys enable row level security;

create policy "mcp_api_keys owner read" on public.mcp_api_keys
  for select using (auth.uid() = user_id);
create policy "mcp_api_keys owner insert" on public.mcp_api_keys
  for insert with check (auth.uid() = user_id);
create policy "mcp_api_keys owner update" on public.mcp_api_keys
  for update using (auth.uid() = user_id);
create policy "mcp_api_keys owner delete" on public.mcp_api_keys
  for delete using (auth.uid() = user_id);

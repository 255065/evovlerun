"""Supabase service-role client. Use server-side only — bypasses RLS."""

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_supabase_admin() -> Client:
    """Service-role Supabase client. Bypasses RLS — never expose to the frontend."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set",
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # V1 has no onboard LLM — the chat assistant (Claude.ai / ChatGPT /
    # Gemini) does the reasoning over our MCP tool surface. The Anthropic
    # and MiniMax client code was deleted; bringing it back is the V2
    # hook for the limiter engine and 4-week reviews.

    # Token encryption for OAuth credentials
    token_encryption_key: str = ""

    # Public URLs (used to build redirect_uri values for OAuth flows)
    frontend_url: str = "http://localhost:3000"
    backend_public_url: str = "http://localhost:8000"

    # Secret used to sign OAuth `state` so providers can echo it back safely.
    oauth_state_secret: str = ""

    # OAuth providers
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_webhook_verify_token: str = ""
    garmin_client_id: str = ""
    garmin_client_secret: str = ""
    oura_client_id: str = ""
    oura_client_secret: str = ""
    whoop_client_id: str = ""
    whoop_client_secret: str = ""

    # Stripe — V1 subscription billing. `stripe_price_id` points at the
    # Product → Price you create in the Stripe dashboard (the single V1 tier).
    # `stripe_webhook_secret` is the signing secret from the Stripe webhook
    # endpoint you create at /billing/webhook on this backend.
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_price_id: str = ""
    stripe_webhook_secret: str = ""
    # When True, /dashboard is hard-gated to subscribed users. Default False
    # for V1 alpha so the founder can ship without paying themselves.
    enforce_subscription: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

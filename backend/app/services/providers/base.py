"""Provider interface contracts.

Every wearable/activity provider must implement ProviderClient. The interface
is intentionally narrow — the goal is that swapping the implementation
(e.g. garth → official Garmin API later) requires only changing one file.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal

Sport = Literal["running", "cycling", "swimming", "strength", "walking", "hiking", "other"]


class ProviderError(Exception):
    """Base class for provider errors. Subclass for specific auth / rate-limit cases."""


class ProviderAuthError(ProviderError):
    """Auth token invalid / expired / revoked. User must reconnect."""


class ProviderRateLimitError(ProviderError):
    """Provider rate-limited us. Retry later."""


@dataclass
class ProviderTokens:
    """Token bundle returned by OAuth completion. Encrypted before DB insert."""

    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scope: str | None = None
    provider_user_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class OAuthFlowResult:
    """Result of starting an OAuth authorization flow."""

    authorize_url: str
    state: str  # opaque value the provider echoes back to the callback


@dataclass
class NormalizedActivity:
    """A workout/activity in EvolveRun's internal shape, ready for `workouts` table."""

    source: str  # provider slug
    source_id: str  # provider's id for this activity
    sport: Sport
    started_at: datetime
    duration_seconds: int
    distance_m: float | None = None
    elevation_gain_m: float | None = None
    avg_hr: int | None = None
    max_hr: int | None = None
    avg_pace_s_per_km: float | None = None
    avg_power_w: float | None = None
    normalized_power_w: float | None = None
    trimp: float | None = None
    tss: float | None = None
    perceived_effort: int | None = None
    notes: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedDailyMetric:
    """A single day's wellness snapshot, ready for `daily_metrics` table."""

    metric_date: date
    resting_hr: int | None = None
    hrv_rmssd: float | None = None
    sleep_minutes: int | None = None
    sleep_score: int | None = None
    readiness_score: int | None = None
    body_battery: int | None = None
    weight_kg: float | None = None
    body_temp_delta: float | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


class ProviderClient(ABC):
    """Protocol every provider implements.

    Implementations should be cheap to construct — connection pooling, token
    refresh, etc. live inside the methods, not the constructor.
    """

    slug: str  # short id used in URLs and the oauth_connections.provider column

    # -- OAuth -------------------------------------------------------------
    @abstractmethod
    def start_oauth(self, *, user_id: str, redirect_uri: str) -> OAuthFlowResult:
        """Begin OAuth. Returns the URL we should redirect the user to."""
        raise NotImplementedError

    @abstractmethod
    async def complete_oauth(
        self, *, code: str, state: str, redirect_uri: str
    ) -> ProviderTokens:
        """Exchange the OAuth code for tokens."""
        raise NotImplementedError

    @abstractmethod
    async def refresh(self, tokens: ProviderTokens) -> ProviderTokens:
        """Refresh an expired access token. May return the same bundle if no refresh needed."""
        raise NotImplementedError

    # -- Data fetch --------------------------------------------------------
    @abstractmethod
    async def fetch_activities(
        self,
        tokens: ProviderTokens,
        *,
        since: datetime,
        until: datetime | None = None,
    ) -> list[NormalizedActivity]:
        """Pull activities in the given time window."""
        raise NotImplementedError

    @abstractmethod
    async def fetch_daily_metrics(
        self,
        tokens: ProviderTokens,
        *,
        since: date,
        until: date | None = None,
    ) -> list[NormalizedDailyMetric]:
        """Pull daily wellness metrics. Implementations that don't have wellness data
        (e.g. Strava) should return []."""
        raise NotImplementedError

    # -- Webhooks ----------------------------------------------------------
    def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        """Verify a webhook signature. Override per provider. Default rejects all."""
        return False

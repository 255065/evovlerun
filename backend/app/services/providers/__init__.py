"""Wearable / activity provider integrations.

Each provider implements the ProviderClient protocol. Registry maps provider
slug → factory so routers and sync workers can dispatch generically.
"""

from app.services.providers.base import (
    CredentialLoginResult,
    NormalizedActivity,
    NormalizedDailyMetric,
    OAuthFlowResult,
    ProviderAuthError,
    ProviderClient,
    ProviderError,
    ProviderRateLimitError,
    ProviderTokens,
)
from app.services.providers.registry import get_provider, list_providers, register_provider

__all__ = [
    "CredentialLoginResult",
    "NormalizedActivity",
    "NormalizedDailyMetric",
    "OAuthFlowResult",
    "ProviderAuthError",
    "ProviderClient",
    "ProviderError",
    "ProviderRateLimitError",
    "ProviderTokens",
    "get_provider",
    "list_providers",
    "register_provider",
]

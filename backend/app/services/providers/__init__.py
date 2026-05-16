"""Wearable / activity provider integrations.

Each provider implements the ProviderClient protocol. Registry maps provider
slug → factory so routers and sync workers can dispatch generically.
"""

from app.services.providers.base import (
    NormalizedActivity,
    NormalizedDailyMetric,
    OAuthFlowResult,
    ProviderClient,
    ProviderError,
    ProviderTokens,
)
from app.services.providers.registry import get_provider, list_providers, register_provider

__all__ = [
    "NormalizedActivity",
    "NormalizedDailyMetric",
    "OAuthFlowResult",
    "ProviderClient",
    "ProviderError",
    "ProviderTokens",
    "get_provider",
    "list_providers",
    "register_provider",
]

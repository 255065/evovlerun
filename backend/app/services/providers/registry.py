"""Provider registry — slug → factory dispatch.

Keep this dumb. Routers and sync workers look providers up by slug; concrete
implementations register themselves at import time.
"""

from typing import Callable

from app.services.providers.base import ProviderClient

_REGISTRY: dict[str, Callable[[], ProviderClient]] = {}


def register_provider(slug: str, factory: Callable[[], ProviderClient]) -> None:
    """Attach a factory to a slug. Called at module import by each provider impl."""
    _REGISTRY[slug] = factory


def get_provider(slug: str) -> ProviderClient:
    """Return a fresh instance of the named provider. Raises KeyError if unknown."""
    if slug not in _REGISTRY:
        raise KeyError(f"Unknown provider: {slug!r}. Registered: {list(_REGISTRY)}")
    return _REGISTRY[slug]()


def list_providers() -> list[str]:
    """All registered provider slugs."""
    return sorted(_REGISTRY.keys())

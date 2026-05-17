"""LLM provider abstraction.

We want to swap between Anthropic, MiniMax, and any future OpenAI-compatible
provider without rewriting business logic. Every reasoning task (limiter
detection, plan generation, daily briefings) goes through `get_llm()` with a
tier — the factory picks the right provider + model from settings.

Three tiers map to the three "weight classes" of work:
  - "deep"      → hardest reasoning (limiter detection, 4-week reviews)
  - "reasoning" → balanced workhorse (plan generation, daily adapter)
  - "bulk"      → cheap classification / summary work

Pick a provider with LLM_PROVIDER in .env. Defaults to anthropic for
backwards compatibility.
"""

from __future__ import annotations

from app.config import get_settings
from app.services.llm.anthropic_client import AnthropicLLM
from app.services.llm.base import LLMClient, LLMToolResult
from app.services.llm.minimax_client import MiniMaxLLM

__all__ = ["get_llm", "LLMClient", "LLMToolResult"]

Tier = str  # "deep" | "reasoning" | "bulk"


def get_llm(tier: Tier = "reasoning") -> LLMClient:
    """Return an LLM client for the given task tier.

    Reads `LLM_PROVIDER` from settings. Validates that the chosen provider has
    its API key configured and raises a clear error otherwise.
    """
    settings = get_settings()
    provider = (settings.llm_provider or "anthropic").lower()

    if provider == "minimax":
        if not settings.minimax_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=minimax but MINIMAX_API_KEY is not set. "
                "Add it to backend/.env."
            )
        model = _pick_model(tier, {
            "deep": settings.minimax_model_deep,
            "reasoning": settings.minimax_model_reasoning,
            "bulk": settings.minimax_model_bulk,
        })
        return MiniMaxLLM(
            api_key=settings.minimax_api_key,
            base_url=settings.minimax_base_url,
            model=model,
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set. "
                "Add it to backend/.env."
            )
        model = _pick_model(tier, {
            "deep": settings.anthropic_model_deep,
            "reasoning": settings.anthropic_model_reasoning,
            "bulk": settings.anthropic_model_bulk,
        })
        return AnthropicLLM(api_key=settings.anthropic_api_key, model=model)

    raise RuntimeError(f"Unknown LLM_PROVIDER: {provider!r}")


def _pick_model(tier: Tier, mapping: dict[str, str]) -> str:
    model = mapping.get(tier)
    if not model:
        # Fall back to "reasoning" tier — it's always populated.
        model = mapping["reasoning"]
    return model

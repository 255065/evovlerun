"""LLM provider contract.

Every implementation must support a single primary operation: send a
system+user prompt with a tool schema, get back the tool's structured input.
We force tool use because structured output is what business logic needs —
free-form text is the exception, not the rule.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMToolResult:
    """Normalized result of a tool-forced LLM call."""

    tool_name: str
    arguments: dict[str, Any]
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    stop_reason: str | None = None
    raw_response: Any = None   # for debugging


class LLMClient(ABC):
    """Minimal interface that limiter/plan/briefing engines code against."""

    model: str

    @abstractmethod
    def call_tool(
        self,
        *,
        system: str,
        user: str,
        tool_name: str,
        tool_description: str,
        tool_schema: dict[str, Any],
        max_tokens: int = 2000,
    ) -> LLMToolResult:
        """Send a prompt and force the model to call exactly one tool.

        Args:
            system: System prompt.
            user: User message.
            tool_name: Name of the tool the model must call.
            tool_description: Brief description for the model.
            tool_schema: JSONSchema for the tool's input.
            max_tokens: Output budget.

        Returns:
            LLMToolResult with the parsed tool arguments.

        Raises:
            RuntimeError if the model fails to call the tool.
        """

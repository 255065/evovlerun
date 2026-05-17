"""Anthropic Claude implementation of the LLM contract."""

from __future__ import annotations

from typing import Any

from anthropic import Anthropic
from anthropic.types import ToolUseBlock

from app.services.llm.base import LLMClient, LLMToolResult


class AnthropicLLM(LLMClient):
    def __init__(self, *, api_key: str, model: str) -> None:
        self._client = Anthropic(api_key=api_key)
        self.model = model

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
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            tools=[{
                "name": tool_name,
                "description": tool_description,
                "input_schema": tool_schema,
            }],
            tool_choice={"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user}],
        )

        tool_blocks = [b for b in response.content if isinstance(b, ToolUseBlock)]
        if not tool_blocks:
            raise RuntimeError(
                f"Anthropic did not call {tool_name!r}. Response content: {response.content}"
            )
        block = tool_blocks[0]

        return LLMToolResult(
            tool_name=block.name,
            arguments=dict(block.input or {}),
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason,
            raw_response=response,
        )

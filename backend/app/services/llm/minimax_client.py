"""MiniMax M2 implementation of the LLM contract.

MiniMax exposes an OpenAI-compatible chat-completions endpoint, so we drive
it through the official `openai` SDK pointed at MiniMax's base URL. Tool
schemas use OpenAI's `function` shape — same JSONSchema as Anthropic, just
wrapped one level deeper.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.services.llm.base import LLMClient, LLMToolResult

log = logging.getLogger(__name__)

# MiniMax thinking models sometimes emit tool calls as XML inside `content`
# instead of populating the OpenAI-standard `tool_calls` array. We detect and
# parse that format as a fallback.
_MINIMAX_TOOL_BLOCK = re.compile(
    r"<minimax:tool_call>\s*<invoke\s+name=\"(?P<name>[^\"]+)\">(?P<body>.*?)</invoke>\s*</minimax:tool_call>",
    re.DOTALL,
)
_MINIMAX_PARAM = re.compile(
    r'<parameter\s+name="(?P<key>[^"]+)">(?P<val>.*?)</parameter>',
    re.DOTALL,
)


class MiniMaxLLM(LLMClient):
    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        # The OpenAI SDK happily talks to any compatible server when we set
        # base_url. MiniMax accepts the same `Authorization: Bearer ...` header.
        self._client = OpenAI(api_key=api_key, base_url=base_url)
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
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_description,
                    "parameters": tool_schema,
                },
            }],
            # Force the model to use the tool. Both "required" and explicit
            # function selection are valid in OpenAI's API; MiniMax follows
            # the same convention.
            tool_choice={"type": "function", "function": {"name": tool_name}},
        )

        choice = response.choices[0]
        msg = choice.message
        usage = response.usage

        # Happy path: OpenAI-standard tool_calls present.
        tool_calls = msg.tool_calls or []
        if tool_calls:
            call = tool_calls[0]
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"MiniMax returned non-JSON tool arguments: {call.function.arguments!r}"
                ) from exc
            return LLMToolResult(
                tool_name=call.function.name,
                arguments=args,
                model=response.model,
                input_tokens=usage.prompt_tokens if usage else None,
                output_tokens=usage.completion_tokens if usage else None,
                stop_reason=choice.finish_reason,
                raw_response=response,
            )

        # Fallback: parse MiniMax's <minimax:tool_call> XML embedded in content.
        parsed = _parse_minimax_xml(msg.content or "", tool_name)
        if parsed is not None:
            return LLMToolResult(
                tool_name=tool_name,
                arguments=parsed,
                model=response.model,
                input_tokens=usage.prompt_tokens if usage else None,
                output_tokens=usage.completion_tokens if usage else None,
                stop_reason=choice.finish_reason,
                raw_response=response,
            )

        # Both paths failed — surface a clear error.
        finish = choice.finish_reason
        hint = ""
        if finish == "length":
            hint = (
                " — finish_reason=length means the model hit max_tokens "
                "before finishing the tool call. Increase max_tokens "
                "(MiniMax M2.5 is a thinking model and needs headroom for reasoning)."
            )
        raise RuntimeError(
            f"MiniMax did not call {tool_name!r}.{hint} "
            f"finish_reason={finish}, content_preview={(msg.content or '')[:300]!r}"
        )


def _parse_minimax_xml(content: str, expected_tool: str) -> dict[str, Any] | None:
    """Parse `<minimax:tool_call><invoke name="..."><parameter>...</parameter>...`.

    Returns the parsed argument dict, or None if the content doesn't contain a
    matching tool block.
    """
    m = _MINIMAX_TOOL_BLOCK.search(content)
    if not m or m.group("name") != expected_tool:
        return None
    body = m.group("body")
    args: dict[str, Any] = {}
    for pm in _MINIMAX_PARAM.finditer(body):
        key = pm.group("key")
        val = pm.group("val").strip()
        # Parameter values are usually JSON literals (arrays, objects, numbers)
        # but sometimes plain strings. Try JSON first.
        try:
            args[key] = json.loads(val)
        except json.JSONDecodeError:
            args[key] = val
    return args or None

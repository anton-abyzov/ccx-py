"""Async OpenAI-compatible API client for OpenRouter and similar providers."""

from __future__ import annotations

import json
import os
import re
from collections.abc import AsyncIterator

import httpx

from ccx.api.types import (
    StreamEvent,
    StreamEventType,
)

_THINK_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def extract_thinking(text: str) -> tuple[str, str]:
    """Extract <think> blocks from text. Returns (clean_text, thinking)."""
    thinking_parts = _THINK_RE.findall(text)
    clean = _THINK_RE.sub("", text)
    return clean, "\n".join(thinking_parts)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenAIClient:
    """Async client for OpenAI-compatible APIs (OpenRouter, etc).

    Converts Anthropic message format to/from OpenAI format so the
    QueryEngine can use it transparently.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "nvidia/nemotron-3-super-120b-a12b:free",
        base_url: str = OPENROUTER_URL,
        max_tokens: int = 8192,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0),
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {self.api_key}",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> OpenAIClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def stream_message(self, request: object) -> AsyncIterator[StreamEvent]:
        """Stream a message request, yielding Anthropic-style StreamEvents."""
        payload = _convert_request(request, self.model, self.max_tokens)
        payload["stream"] = True

        async with self._client.stream(
            "POST", self.base_url, json=payload
        ) as response:
            if response.status_code != 200:
                body = await response.aread()
                raise RuntimeError(f"OpenAI API error {response.status_code}: {body.decode()}")

            started = False
            text_started = False
            thinking_started = False
            block_idx = 0
            active_tools: dict[int, int] = {}  # openai tool idx -> block idx

            async for line in response.aiter_lines():
                line = line.strip()
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data: "):
                    continue

                data = line[6:]  # strip "data: "
                if data == "[DONE]":
                    if started:
                        if thinking_started:
                            yield StreamEvent(
                                type=StreamEventType.CONTENT_BLOCK_STOP,
                                index=block_idx,
                            )
                        if text_started:
                            yield StreamEvent(
                                type=StreamEventType.CONTENT_BLOCK_STOP,
                                index=block_idx,
                            )
                        yield StreamEvent(
                            type=StreamEventType.MESSAGE_DELTA,
                            delta={"stop_reason": "end_turn"},
                        )
                        yield StreamEvent(type=StreamEventType.MESSAGE_STOP)
                    return

                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue

                # Emit message_start on first chunk
                if not started:
                    started = True
                    yield StreamEvent(
                        type=StreamEventType.MESSAGE_START,
                        message={
                            "id": chunk.get("id", ""),
                            "type": "message",
                            "role": "assistant",
                            "model": chunk.get("model", self.model),
                            "usage": {"input_tokens": 0, "output_tokens": 0},
                        },
                    )

                choices = chunk.get("choices", [])
                if not choices:
                    usage = chunk.get("usage")
                    if usage:
                        yield StreamEvent(
                            type=StreamEventType.MESSAGE_DELTA,
                            usage={"output_tokens": usage.get("completion_tokens", 0)},
                        )
                    continue

                choice = choices[0]
                delta = choice.get("delta", {})
                finish_reason = choice.get("finish_reason")

                # Reasoning content (OpenRouter DeepSeek R1 etc.)
                reasoning = delta.get("reasoning_content") or delta.get("reasoning", "")
                if reasoning:
                    if not thinking_started:
                        thinking_started = True
                        # Close text block if open before starting thinking
                        if text_started:
                            yield StreamEvent(
                                type=StreamEventType.CONTENT_BLOCK_STOP,
                                index=block_idx,
                            )
                            block_idx += 1
                            text_started = False
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_START,
                            index=block_idx,
                            content_block={"type": "thinking"},
                        )
                    yield StreamEvent(
                        type=StreamEventType.CONTENT_BLOCK_DELTA,
                        index=block_idx,
                        delta={"type": "thinking_delta", "thinking": reasoning},
                    )

                # Text content
                content = delta.get("content", "")
                if content:
                    # Close thinking block if open before starting text
                    if thinking_started:
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_STOP,
                            index=block_idx,
                        )
                        block_idx += 1
                        thinking_started = False

                    # Check for <think> tags in text
                    clean, thinking_text = extract_thinking(content)

                    if thinking_text:
                        # Emit thinking block for extracted tags
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_START,
                            index=block_idx,
                            content_block={"type": "thinking"},
                        )
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_DELTA,
                            index=block_idx,
                            delta={"type": "thinking_delta", "thinking": thinking_text},
                        )
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_STOP,
                            index=block_idx,
                        )
                        block_idx += 1
                        content = clean

                    if content:
                        if not text_started:
                            text_started = True
                            yield StreamEvent(
                                type=StreamEventType.CONTENT_BLOCK_START,
                                index=block_idx,
                                content_block={"type": "text"},
                            )
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_DELTA,
                            index=block_idx,
                            delta={"type": "text_delta", "text": content},
                        )

                # Tool calls
                for tc in delta.get("tool_calls", []):
                    tc_idx = tc.get("index", 0)
                    if tc_idx not in active_tools:
                        # Close text block if open
                        if text_started:
                            yield StreamEvent(
                                type=StreamEventType.CONTENT_BLOCK_STOP,
                                index=block_idx,
                            )
                            block_idx += 1
                            text_started = False
                        active_tools[tc_idx] = block_idx
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_START,
                            index=block_idx,
                            content_block={
                                "type": "tool_use",
                                "id": tc.get("id", ""),
                                "name": tc.get("function", {}).get("name", ""),
                            },
                        )

                    args = tc.get("function", {}).get("arguments", "")
                    if args:
                        idx = active_tools[tc_idx]
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_DELTA,
                            index=idx,
                            delta={"type": "input_json_delta", "partial_json": args},
                        )

                # Finish reason
                if finish_reason:
                    if thinking_started:
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_STOP,
                            index=block_idx,
                        )
                        thinking_started = False
                    if text_started:
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_STOP,
                            index=block_idx,
                        )
                        text_started = False
                    for idx in active_tools.values():
                        yield StreamEvent(
                            type=StreamEventType.CONTENT_BLOCK_STOP,
                            index=idx,
                        )

                    stop_reason = "end_turn"
                    if finish_reason == "tool_calls":
                        stop_reason = "tool_use"
                    elif finish_reason == "length":
                        stop_reason = "max_tokens"

                    yield StreamEvent(
                        type=StreamEventType.MESSAGE_DELTA,
                        delta={"stop_reason": stop_reason},
                    )
                    yield StreamEvent(type=StreamEventType.MESSAGE_STOP)
                    return

    async def send_message(self, request: object) -> object:
        """Send a non-streaming message request."""
        from ccx.api.types import MessageResponse, Role, StopReason, TextContent, ThinkingContent, ToolUseContent, Usage

        payload = _convert_request(request, self.model, self.max_tokens)
        payload["stream"] = False

        response = await self._client.post(self.base_url, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text}")

        data = response.json()
        choices = data.get("choices", [])
        usage_data = data.get("usage", {})

        content = []
        stop_reason = StopReason.END_TURN
        if choices:
            choice = choices[0]
            msg = choice.get("message", {})
            # Reasoning content (OpenRouter DeepSeek R1 etc.)
            reasoning = msg.get("reasoning_content") or msg.get("reasoning", "")
            if reasoning:
                content.append(ThinkingContent(thinking=reasoning))
            if msg.get("content"):
                text = msg["content"]
                clean, thinking_text = extract_thinking(text)
                if thinking_text:
                    content.append(ThinkingContent(thinking=thinking_text))
                if clean:
                    content.append(TextContent(text=clean))
            elif not reasoning:
                pass  # no text content
            for tc in msg.get("tool_calls", []):
                fn = tc.get("function", {})
                try:
                    tool_input = json.loads(fn.get("arguments", "{}"))
                except json.JSONDecodeError:
                    tool_input = {}
                content.append(ToolUseContent(
                    id=tc.get("id", ""),
                    name=fn.get("name", ""),
                    input=tool_input,
                ))
            fr = choice.get("finish_reason", "stop")
            if fr == "tool_calls":
                stop_reason = StopReason.TOOL_USE
            elif fr == "length":
                stop_reason = StopReason.MAX_TOKENS

        return MessageResponse(
            id=data.get("id", ""),
            content=content,
            stop_reason=stop_reason,
            usage=Usage(
                input_tokens=usage_data.get("prompt_tokens", 0),
                output_tokens=usage_data.get("completion_tokens", 0),
            ),
        )


def _convert_request(request: object, default_model: str, default_max_tokens: int) -> dict:
    """Convert an Anthropic MessageRequest to OpenAI chat completion format."""
    req_data = request.model_dump(exclude_none=True)
    messages = []

    # System prompt
    system = req_data.get("system")
    if system:
        messages.append({"role": "system", "content": system})

    # Convert messages
    for msg in req_data.get("messages", []):
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # String content (simple user message)
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
            continue

        # Array content (Anthropic-style blocks)
        if role == "user":
            text_parts = []
            for block in content:
                block_type = block.get("type", "")
                if block_type == "text":
                    text_parts.append(block.get("text", ""))
                elif block_type == "tool_result":
                    result_content = block.get("content", "")
                    if block.get("is_error"):
                        result_content = f"ERROR: {result_content}"
                    messages.append({
                        "role": "tool",
                        "content": result_content,
                        "tool_call_id": block.get("tool_use_id", ""),
                    })
            if text_parts:
                messages.append({"role": "user", "content": "\n".join(text_parts)})

        elif role == "assistant":
            oai_msg: dict = {"role": "assistant"}
            text_parts = []
            tool_calls = []
            for block in content:
                block_type = block.get("type", "")
                if block_type == "text":
                    text_parts.append(block.get("text", ""))
                elif block_type == "tool_use":
                    inp = block.get("input", {})
                    tool_calls.append({
                        "id": block.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": json.dumps(inp) if isinstance(inp, dict) else str(inp),
                        },
                    })
            if text_parts:
                oai_msg["content"] = "\n".join(text_parts)
            if tool_calls:
                oai_msg["tool_calls"] = tool_calls
            messages.append(oai_msg)

    # Convert tools
    tools = []
    for t in req_data.get("tools", []):
        tools.append({
            "type": "function",
            "function": {
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {}),
            },
        })

    result: dict = {
        "model": req_data.get("model") or default_model,
        "messages": messages,
        "max_tokens": req_data.get("max_tokens") or default_max_tokens,
    }
    if tools:
        result["tools"] = tools

    return result

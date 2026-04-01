"""Async Claude API client with streaming support."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import httpx

from ccx.api.stream import parse_sse
from ccx.api.types import (
    MessageRequest,
    MessageResponse,
    StreamEvent,
    StreamEventType,
    StopReason,
    Usage,
)

MESSAGES_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class APIError(Exception):
    """Raised when the Claude API returns an error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"API error {status_code}: {message}")


class ClaudeClient:
    """Async client for the Claude Messages API with streaming."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
        base_url: str = MESSAGES_URL,
        max_tokens: int = 8192,
        *,
        use_oauth: bool = False,
    ) -> None:
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.use_oauth = use_oauth

        headers: dict[str, str] = {
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        if use_oauth:
            headers["authorization"] = f"Bearer {self.api_key}"
            headers["anthropic-beta"] = "oauth-2025-04-20"
        else:
            headers["x-api-key"] = self.api_key

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0),
            headers=headers,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> ClaudeClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def stream_message(
        self, request: MessageRequest
    ) -> AsyncIterator[StreamEvent]:
        """Stream a message request, yielding SSE events."""
        payload = request.model_dump(exclude_none=True)
        payload["stream"] = True
        if not payload.get("model"):
            payload["model"] = self.model
        if not payload.get("max_tokens"):
            payload["max_tokens"] = self.max_tokens

        async with self._client.stream(
            "POST", self.base_url, json=payload
        ) as response:
            if response.status_code != 200:
                body = await response.aread()
                raise APIError(response.status_code, body.decode())
            async for event in parse_sse(response.aiter_lines()):
                yield event

    async def send_message(self, request: MessageRequest) -> MessageResponse:
        """Send a non-streaming message request."""
        payload = request.model_dump(exclude_none=True)
        payload["stream"] = False
        if not payload.get("model"):
            payload["model"] = self.model
        if not payload.get("max_tokens"):
            payload["max_tokens"] = self.max_tokens

        response = await self._client.post(self.base_url, json=payload)
        if response.status_code != 200:
            raise APIError(response.status_code, response.text)
        return MessageResponse.model_validate(response.json())

    def build_response_from_stream(
        self, events: list[StreamEvent]
    ) -> MessageResponse:
        """Reconstruct a MessageResponse from collected stream events."""
        resp = MessageResponse()
        for event in events:
            match event.type:
                case StreamEventType.MESSAGE_START:
                    if event.message:
                        resp.id = event.message.get("id", "")
                        usage_data = event.message.get("usage", {})
                        resp.usage = Usage(**usage_data) if usage_data else Usage()
                case StreamEventType.MESSAGE_DELTA:
                    if event.delta:
                        sr = event.delta.get("stop_reason")
                        if sr:
                            resp.stop_reason = StopReason(sr)
                    if event.usage:
                        resp.usage.output_tokens = event.usage.get(
                            "output_tokens", resp.usage.output_tokens
                        )
        return resp

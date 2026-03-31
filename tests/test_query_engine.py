"""Tests for the query engine (unit tests with mocked API)."""

import pytest

from ccx.api.types import (
    Message,
    MessageRequest,
    Role,
    StreamEvent,
    StreamEventType,
)
from ccx.core.context import SessionContext
from ccx.core.query import QueryEngine
from ccx.tools.registry import ToolRegistry


class MockClient:
    """Mock Claude client that returns pre-configured events."""

    def __init__(self, events: list[list[StreamEvent]]) -> None:
        self._responses = iter(events)

    async def stream_message(self, request: MessageRequest):
        events = next(self._responses)
        for event in events:
            yield event


def _text_response(text: str) -> list[StreamEvent]:
    """Create stream events for a simple text response."""
    return [
        StreamEvent(
            type=StreamEventType.MESSAGE_START,
            message={"id": "msg_1", "usage": {"input_tokens": 10}},
        ),
        StreamEvent(
            type=StreamEventType.CONTENT_BLOCK_START,
            content_block={"type": "text"},
        ),
        StreamEvent(
            type=StreamEventType.CONTENT_BLOCK_DELTA,
            delta={"type": "text_delta", "text": text},
        ),
        StreamEvent(type=StreamEventType.CONTENT_BLOCK_STOP),
        StreamEvent(
            type=StreamEventType.MESSAGE_DELTA,
            delta={"stop_reason": "end_turn"},
            usage={"output_tokens": 5},
        ),
        StreamEvent(type=StreamEventType.MESSAGE_STOP),
    ]


@pytest.mark.asyncio
async def test_simple_text_response():
    client = MockClient([_text_response("Hello world")])
    context = SessionContext()
    context.add_user_message("hi")

    captured_text = []
    engine = QueryEngine(
        client=client,
        registry=ToolRegistry(),
        context=context,
        on_text=lambda t: captured_text.append(t),
    )
    blocks = await engine.run()
    assert len(blocks) == 1
    assert blocks[0].text == "Hello world"
    assert captured_text == ["Hello world"]


@pytest.mark.asyncio
async def test_token_tracking():
    client = MockClient([_text_response("ok")])
    context = SessionContext()
    context.add_user_message("test")

    engine = QueryEngine(
        client=client,
        registry=ToolRegistry(),
        context=context,
    )
    await engine.run()
    assert context.total_input_tokens == 10
    assert context.total_output_tokens == 5

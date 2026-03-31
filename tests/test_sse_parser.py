"""Tests for SSE parser."""

import pytest

from ccx.api.stream import SSEEvent, parse_sse
from ccx.api.types import StreamEventType


async def _lines(data: list[str]):
    """Helper: yield lines as an async iterator."""
    for line in data:
        yield line


@pytest.mark.asyncio
async def test_parse_simple_text_event():
    lines = [
        "event: content_block_delta\n",
        'data: {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "hi"}}\n',
        "\n",
    ]
    events = [e async for e in parse_sse(_lines(lines))]
    assert len(events) == 1
    assert events[0].type == StreamEventType.CONTENT_BLOCK_DELTA
    assert events[0].delta["text"] == "hi"


@pytest.mark.asyncio
async def test_parse_message_start():
    lines = [
        "event: message_start\n",
        'data: {"type": "message_start", "message": {"id": "msg_1", "usage": {"input_tokens": 10}}}\n',
        "\n",
    ]
    events = [e async for e in parse_sse(_lines(lines))]
    assert len(events) == 1
    assert events[0].type == StreamEventType.MESSAGE_START
    assert events[0].message["id"] == "msg_1"


@pytest.mark.asyncio
async def test_parse_ping_event():
    lines = [
        "event: ping\n",
        'data: {"type": "ping"}\n',
        "\n",
    ]
    events = [e async for e in parse_sse(_lines(lines))]
    assert len(events) == 1
    assert events[0].type == StreamEventType.PING


@pytest.mark.asyncio
async def test_ignore_comments():
    lines = [
        ": this is a comment\n",
        "event: ping\n",
        'data: {"type": "ping"}\n',
        "\n",
    ]
    events = [e async for e in parse_sse(_lines(lines))]
    assert len(events) == 1


@pytest.mark.asyncio
async def test_multiline_data():
    lines = [
        "event: content_block_delta\n",
        'data: {"type": "content_block_delta",\n',
        'data:  "delta": {"type": "text_delta", "text": "ok"}}\n',
        "\n",
    ]
    events = [e async for e in parse_sse(_lines(lines))]
    assert len(events) == 1


@pytest.mark.asyncio
async def test_empty_stream():
    events = [e async for e in parse_sse(_lines([]))]
    assert len(events) == 0


@pytest.mark.asyncio
async def test_trailing_event_without_newline():
    lines = [
        "event: ping\n",
        'data: {"type": "ping"}\n',
    ]
    events = [e async for e in parse_sse(_lines(lines))]
    assert len(events) == 1


@pytest.mark.asyncio
async def test_invalid_json_skipped():
    lines = [
        "event: content_block_delta\n",
        "data: not-json\n",
        "\n",
    ]
    events = [e async for e in parse_sse(_lines(lines))]
    assert len(events) == 0


def test_sse_event_finalize():
    evt = SSEEvent()
    evt.append_data('{"a": 1}')
    evt.finalize()
    assert evt.data == '{"a": 1}'


def test_sse_event_multiline_finalize():
    evt = SSEEvent()
    evt.append_data('{"a":')
    evt.append_data(' 1}')
    evt.finalize()
    assert evt.data == '{"a":\n 1}'

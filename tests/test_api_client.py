"""Tests for the Claude API client."""

import pytest

from ccx.api.client import ClaudeClient, APIError
from ccx.api.types import (
    MessageResponse,
    StreamEvent,
    StreamEventType,
    StopReason,
    Usage,
)


def test_client_init_defaults():
    client = ClaudeClient(api_key="test-key")
    assert client.api_key == "test-key"
    assert client.model == "claude-sonnet-4-6"
    assert client.max_tokens == 8192


def test_client_init_custom():
    client = ClaudeClient(
        api_key="key",
        model="claude-opus-4-6",
        max_tokens=4096,
    )
    assert client.model == "claude-opus-4-6"
    assert client.max_tokens == 4096


def test_api_error():
    err = APIError(401, "unauthorized")
    assert err.status_code == 401
    assert "401" in str(err)
    assert "unauthorized" in str(err)


def test_build_response_from_stream():
    client = ClaudeClient(api_key="test")
    events = [
        StreamEvent(
            type=StreamEventType.MESSAGE_START,
            message={"id": "msg_123", "usage": {"input_tokens": 50}},
        ),
        StreamEvent(
            type=StreamEventType.CONTENT_BLOCK_DELTA,
            delta={"type": "text_delta", "text": "hello"},
        ),
        StreamEvent(
            type=StreamEventType.MESSAGE_DELTA,
            delta={"stop_reason": "end_turn"},
            usage={"output_tokens": 10},
        ),
    ]
    resp = client.build_response_from_stream(events)
    assert resp.id == "msg_123"
    assert resp.stop_reason == StopReason.END_TURN
    assert resp.usage.input_tokens == 50
    assert resp.usage.output_tokens == 10


def test_build_response_empty_events():
    client = ClaudeClient(api_key="test")
    resp = client.build_response_from_stream([])
    assert resp.id == ""
    assert resp.stop_reason is None

"""Tests for API type models."""

from ccx.api.types import (
    ContentBlock,
    Message,
    MessageRequest,
    MessageResponse,
    Role,
    StopReason,
    StreamEvent,
    StreamEventType,
    TextContent,
    ThinkingContent,
    ToolResultContent,
    ToolUseContent,
    Usage,
)


def test_text_content():
    tc = TextContent(text="hello")
    assert tc.type == "text"
    assert tc.text == "hello"


def test_thinking_content():
    tc = ThinkingContent(thinking="let me think")
    assert tc.type == "thinking"


def test_tool_use_content():
    tu = ToolUseContent(id="tu_1", name="bash", input={"command": "ls"})
    assert tu.type == "tool_use"
    assert tu.name == "bash"
    assert tu.input["command"] == "ls"


def test_tool_result_content():
    tr = ToolResultContent(tool_use_id="tu_1", content="output")
    assert tr.type == "tool_result"
    assert not tr.is_error


def test_tool_result_error():
    tr = ToolResultContent(tool_use_id="tu_1", content="fail", is_error=True)
    assert tr.is_error


def test_message():
    msg = Message(role=Role.USER, content="hello")
    assert msg.role == Role.USER
    assert msg.content == "hello"


def test_message_with_blocks():
    msg = Message(
        role=Role.ASSISTANT,
        content=[TextContent(text="hi"), TextContent(text="there")],
    )
    assert len(msg.content) == 2


def test_message_request_defaults():
    req = MessageRequest(messages=[Message(role=Role.USER, content="hi")])
    assert req.model == "claude-sonnet-4-6"
    assert req.max_tokens == 8192
    assert req.stream is True
    assert req.tools == []


def test_message_response_defaults():
    resp = MessageResponse()
    assert resp.id == ""
    assert resp.stop_reason is None
    assert resp.usage.input_tokens == 0


def test_stream_event():
    evt = StreamEvent(
        type=StreamEventType.CONTENT_BLOCK_DELTA,
        delta={"type": "text_delta", "text": "hello"},
    )
    assert evt.type == StreamEventType.CONTENT_BLOCK_DELTA
    assert evt.delta["text"] == "hello"


def test_usage():
    u = Usage(input_tokens=100, output_tokens=50)
    assert u.input_tokens == 100
    assert u.output_tokens == 50


def test_stop_reasons():
    assert StopReason.END_TURN == "end_turn"
    assert StopReason.TOOL_USE == "tool_use"
    assert StopReason.MAX_TOKENS == "max_tokens"

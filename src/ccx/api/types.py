"""Pydantic models for the Claude Messages API."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class StopReason(str, Enum):
    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ThinkingContent(BaseModel):
    type: Literal["thinking"] = "thinking"
    thinking: str


class ToolUseContent(BaseModel):
    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any]


class ToolResultContent(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str
    is_error: bool = False


ContentBlock = TextContent | ThinkingContent | ToolUseContent | ToolResultContent


class Message(BaseModel):
    role: Role
    content: list[ContentBlock] | str


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]


class MessageRequest(BaseModel):
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 8192
    messages: list[Message]
    tools: list[ToolDefinition] = Field(default_factory=list)
    system: str | None = None
    stream: bool = True


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class MessageResponse(BaseModel):
    id: str = ""
    type: str = "message"
    role: Role = Role.ASSISTANT
    content: list[ContentBlock] = Field(default_factory=list)
    stop_reason: StopReason | None = None
    usage: Usage = Field(default_factory=Usage)


class StreamEventType(str, Enum):
    MESSAGE_START = "message_start"
    CONTENT_BLOCK_START = "content_block_start"
    CONTENT_BLOCK_DELTA = "content_block_delta"
    CONTENT_BLOCK_STOP = "content_block_stop"
    MESSAGE_DELTA = "message_delta"
    MESSAGE_STOP = "message_stop"
    PING = "ping"
    ERROR = "error"


class StreamEvent(BaseModel):
    type: StreamEventType
    index: int | None = None
    message: dict[str, Any] | None = None
    content_block: dict[str, Any] | None = None
    delta: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

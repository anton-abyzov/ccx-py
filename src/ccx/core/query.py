"""Query engine: the async agentic loop that drives conversation."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from typing import Any

from ccx.api.client import ClaudeClient
from ccx.api.types import (
    ContentBlock,
    Message,
    MessageRequest,
    Role,
    StreamEvent,
    StreamEventType,
    TextContent,
    ThinkingContent,
    ToolResultContent,
    ToolUseContent,
)
from ccx.core.context import SessionContext
from ccx.permissions.classifier import PermissionClassifier
from ccx.permissions.modes import PermissionMode
from ccx.tools.registry import ToolRegistry

# Callback types
OnText = Callable[[str], Any]
OnThinking = Callable[[str], Any]
OnToolUse = Callable[[str, str, dict[str, Any]], Any]
OnToolResult = Callable[[str, str, bool], Any]

MAX_TOOL_LOOPS = 50


class QueryEngine:
    """Drives the agentic loop: send messages, handle tool use, repeat."""

    def __init__(
        self,
        client: ClaudeClient,
        registry: ToolRegistry,
        context: SessionContext,
        permission_mode: PermissionMode = PermissionMode.DEFAULT,
        on_text: OnText | None = None,
        on_thinking: OnThinking | None = None,
        on_tool_use: OnToolUse | None = None,
        on_tool_result: OnToolResult | None = None,
    ) -> None:
        self.client = client
        self.registry = registry
        self.context = context
        self.permission_mode = permission_mode
        self._classifier = PermissionClassifier()
        self._on_text = on_text
        self._on_thinking = on_thinking
        self._on_tool_use = on_tool_use
        self._on_tool_result = on_tool_result

    async def run(self) -> list[ContentBlock]:
        """Run the agentic loop until the model stops requesting tools."""
        all_content: list[ContentBlock] = []

        for _ in range(MAX_TOOL_LOOPS):
            request = MessageRequest(
                model=self.context.model,
                max_tokens=self.context.max_tokens,
                messages=self.context.messages,
                tools=self.registry.to_api_schemas(),
                system=self.context.system_prompt or None,
            )

            content_blocks, tool_uses = await self._stream_response(request)
            all_content.extend(content_blocks)

            # Add assistant response to conversation
            self.context.add_assistant_message(content_blocks)

            if not tool_uses:
                break

            # Execute tools in parallel
            results = await asyncio.gather(
                *[self._execute_tool(tu) for tu in tool_uses]
            )

            # Add tool results to conversation
            for tu, result in zip(tool_uses, results):
                self.context.add_tool_result(tu.id, result.content, result.is_error)

        return all_content

    async def _stream_response(
        self, request: MessageRequest
    ) -> tuple[list[ContentBlock], list[ToolUseContent]]:
        """Stream a response, collecting content blocks and tool uses."""
        content_blocks: list[ContentBlock] = []
        tool_uses: list[ToolUseContent] = []

        current_text = ""
        current_thinking = ""
        current_tool: dict[str, Any] | None = None
        current_tool_json = ""

        async for event in self.client.stream_message(request):
            match event.type:
                case StreamEventType.MESSAGE_START:
                    if event.message and "usage" in event.message:
                        usage = event.message["usage"]
                        self.context.total_input_tokens += usage.get("input_tokens", 0)

                case StreamEventType.CONTENT_BLOCK_START:
                    if event.content_block:
                        block_type = event.content_block.get("type", "")
                        if block_type == "tool_use":
                            current_tool = event.content_block
                            current_tool_json = ""
                        elif block_type == "thinking":
                            current_thinking = ""

                case StreamEventType.CONTENT_BLOCK_DELTA:
                    if event.delta:
                        delta_type = event.delta.get("type", "")
                        if delta_type == "text_delta":
                            text = event.delta.get("text", "")
                            current_text += text
                            if self._on_text:
                                self._on_text(text)
                        elif delta_type == "thinking_delta":
                            thinking = event.delta.get("thinking", "")
                            current_thinking += thinking
                            if self._on_thinking:
                                self._on_thinking(thinking)
                        elif delta_type == "input_json_delta":
                            current_tool_json += event.delta.get("partial_json", "")

                case StreamEventType.CONTENT_BLOCK_STOP:
                    if current_text:
                        content_blocks.append(TextContent(text=current_text))
                        current_text = ""
                    if current_thinking:
                        content_blocks.append(ThinkingContent(thinking=current_thinking))
                        current_thinking = ""
                    if current_tool is not None:
                        import json

                        try:
                            tool_input = json.loads(current_tool_json) if current_tool_json else {}
                        except json.JSONDecodeError:
                            tool_input = {}
                        tu = ToolUseContent(
                            id=current_tool.get("id", ""),
                            name=current_tool.get("name", ""),
                            input=tool_input,
                        )
                        content_blocks.append(tu)
                        tool_uses.append(tu)
                        if self._on_tool_use:
                            self._on_tool_use(tu.name, tu.id, tu.input)
                        current_tool = None

                case StreamEventType.MESSAGE_DELTA:
                    if event.usage:
                        self.context.total_output_tokens += event.usage.get("output_tokens", 0)

        return content_blocks, tool_uses

    async def _execute_tool(self, tool_use: ToolUseContent) -> ToolResultContent:
        """Execute a single tool call and return the result."""
        result = await self.registry.execute(
            tool_use.name, tool_use.input, self.context.tool_context
        )

        if self._on_tool_result:
            self._on_tool_result(tool_use.name, result.output, result.is_error)

        return ToolResultContent(
            tool_use_id=tool_use.id,
            content=result.output,
            is_error=result.is_error,
        )

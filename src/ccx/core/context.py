"""Session context: manages conversation state and tool context."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ccx.api.types import ContentBlock, Message, Role
from ccx.tools.base import ToolContext


@dataclass
class SessionContext:
    """Holds the state for a single interactive session."""

    working_dir: Path = field(default_factory=Path.cwd)
    messages: list[Message] = field(default_factory=list)
    system_prompt: str = ""
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 8192
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    @property
    def tool_context(self) -> ToolContext:
        return ToolContext(working_dir=self.working_dir)

    def add_user_message(self, text: str) -> None:
        self.messages.append(Message(role=Role.USER, content=text))

    def add_assistant_message(self, content: list[ContentBlock]) -> None:
        self.messages.append(Message(role=Role.ASSISTANT, content=content))

    def add_tool_result(self, tool_use_id: str, output: str, is_error: bool = False) -> None:
        from ccx.api.types import ToolResultContent

        block = ToolResultContent(
            tool_use_id=tool_use_id,
            content=output,
            is_error=is_error,
        )
        self.messages.append(Message(role=Role.USER, content=[block]))

    @property
    def token_count(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

"""MicroCompact: aggressive context compression."""

from __future__ import annotations

from ccx.api.types import (
    ContentBlock,
    Message,
    Role,
    TextContent,
    ToolResultContent,
    ToolUseContent,
)
from ccx.compact.tokens import estimate_message_tokens

# If tool output exceeds this, truncate it
MAX_TOOL_OUTPUT_TOKENS = 2000
# Keep at most N chars of tool output after compaction
TRUNCATED_OUTPUT_CHARS = 4000


class MicroCompact:
    """Aggressive compaction that truncates tool results and collapses turns."""

    def compact(self, messages: list[Message], budget_tokens: int) -> list[Message]:
        """Compact messages to fit within token budget.

        Strategy:
        1. Always keep the first user message (original prompt)
        2. Always keep the last 4 messages (current context)
        3. Truncate large tool results in middle messages
        4. Collapse sequential assistant text blocks
        """
        if not messages:
            return messages

        total = sum(estimate_message_tokens(m) for m in messages)
        if total <= budget_tokens:
            return messages

        # Phase 1: Truncate tool results
        compacted = []
        for i, msg in enumerate(messages):
            if i < 1 or i >= len(messages) - 4:
                compacted.append(msg)
                continue

            if isinstance(msg.content, list):
                new_blocks: list[ContentBlock] = []
                for block in msg.content:
                    if isinstance(block, ToolResultContent):
                        if len(block.content) > TRUNCATED_OUTPUT_CHARS:
                            new_blocks.append(
                                ToolResultContent(
                                    tool_use_id=block.tool_use_id,
                                    content=block.content[:TRUNCATED_OUTPUT_CHARS]
                                    + "\n... (compacted)",
                                    is_error=block.is_error,
                                )
                            )
                        else:
                            new_blocks.append(block)
                    else:
                        new_blocks.append(block)
                compacted.append(Message(role=msg.role, content=new_blocks))
            else:
                compacted.append(msg)

        # Phase 2: If still over budget, drop middle messages
        total = sum(estimate_message_tokens(m) for m in compacted)
        if total > budget_tokens and len(compacted) > 6:
            keep_start = compacted[:2]
            keep_end = compacted[-4:]
            summary = Message(
                role=Role.USER,
                content="[Earlier conversation compacted to save context]",
            )
            compacted = keep_start + [summary] + keep_end

        return compacted

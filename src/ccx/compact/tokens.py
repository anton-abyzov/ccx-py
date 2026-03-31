"""Token estimation utilities."""

from __future__ import annotations

from ccx.api.types import ContentBlock, Message, TextContent, ToolResultContent, ToolUseContent

# Rough estimate: ~4 chars per token for English text
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count from text length."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def estimate_message_tokens(message: Message) -> int:
    """Estimate tokens in a single message."""
    if isinstance(message.content, str):
        return estimate_tokens(message.content)

    total = 0
    for block in message.content:
        match block:
            case TextContent(text=text):
                total += estimate_tokens(text)
            case ToolUseContent(input=inp):
                total += estimate_tokens(str(inp)) + 20  # overhead for tool metadata
            case ToolResultContent(content=content):
                total += estimate_tokens(content)
            case _:
                total += 50  # default estimate for unknown blocks
    return total


def estimate_conversation_tokens(messages: list[Message]) -> int:
    """Estimate total tokens across all messages."""
    return sum(estimate_message_tokens(m) for m in messages)

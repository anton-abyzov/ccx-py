"""Tests for the compaction system."""

import pytest

from ccx.api.types import Message, Role, TextContent, ToolResultContent
from ccx.compact.auto import AutoCompact
from ccx.compact.micro import MicroCompact
from ccx.compact.tokens import (
    estimate_conversation_tokens,
    estimate_message_tokens,
    estimate_tokens,
)


class TestTokenEstimation:
    def test_estimate_tokens(self):
        assert estimate_tokens("") == 1  # minimum 1
        assert estimate_tokens("hello") >= 1
        assert estimate_tokens("a" * 100) == 25  # 100/4

    def test_estimate_message_tokens_string(self):
        msg = Message(role=Role.USER, content="hello world")
        tokens = estimate_message_tokens(msg)
        assert tokens >= 1

    def test_estimate_message_tokens_blocks(self):
        msg = Message(
            role=Role.ASSISTANT,
            content=[TextContent(text="hello"), TextContent(text="world")],
        )
        tokens = estimate_message_tokens(msg)
        assert tokens >= 2

    def test_estimate_conversation(self):
        messages = [
            Message(role=Role.USER, content="hello"),
            Message(role=Role.ASSISTANT, content="world"),
        ]
        tokens = estimate_conversation_tokens(messages)
        assert tokens >= 2


class TestMicroCompact:
    def test_no_compaction_needed(self):
        mc = MicroCompact()
        messages = [
            Message(role=Role.USER, content="hi"),
            Message(role=Role.ASSISTANT, content="hello"),
        ]
        result = mc.compact(messages, budget_tokens=1000)
        assert len(result) == 2

    def test_truncate_tool_results(self):
        mc = MicroCompact()
        messages = [
            Message(role=Role.USER, content="start"),
            Message(role=Role.ASSISTANT, content="ok"),
            Message(
                role=Role.USER,
                content=[
                    ToolResultContent(
                        tool_use_id="t1",
                        content="x" * 10000,
                    )
                ],
            ),
            Message(role=Role.ASSISTANT, content="noted"),
            Message(role=Role.USER, content="continue"),
            Message(role=Role.ASSISTANT, content="done"),
        ]
        result = mc.compact(messages, budget_tokens=100)
        assert len(result) <= len(messages)

    def test_empty_messages(self):
        mc = MicroCompact()
        result = mc.compact([], budget_tokens=100)
        assert result == []


class TestAutoCompact:
    def test_no_compact_below_threshold(self):
        ac = AutoCompact(max_context_tokens=10000)
        messages = [Message(role=Role.USER, content="hi")]
        assert not ac.should_compact(messages)
        result = ac.maybe_compact(messages)
        assert result == messages

    def test_compact_above_threshold(self):
        ac = AutoCompact(max_context_tokens=100, threshold_ratio=0.1)
        messages = [
            Message(role=Role.USER, content="x" * 500),
            Message(role=Role.ASSISTANT, content="y" * 500),
        ]
        assert ac.should_compact(messages)
        result = ac.maybe_compact(messages)
        assert ac.compaction_count == 1

    def test_threshold_tokens(self):
        ac = AutoCompact(max_context_tokens=10000, threshold_ratio=0.8)
        assert ac.threshold_tokens == 8000

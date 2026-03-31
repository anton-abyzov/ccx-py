"""AutoCompact: automatic context management triggered by token thresholds."""

from __future__ import annotations

from ccx.api.types import Message
from ccx.compact.micro import MicroCompact
from ccx.compact.tokens import estimate_conversation_tokens

# Default threshold: compact when we exceed 80% of max context
DEFAULT_THRESHOLD_RATIO = 0.8
DEFAULT_MAX_CONTEXT_TOKENS = 200_000


class AutoCompact:
    """Monitors conversation size and triggers compaction automatically."""

    def __init__(
        self,
        max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
        threshold_ratio: float = DEFAULT_THRESHOLD_RATIO,
    ) -> None:
        self.max_context_tokens = max_context_tokens
        self.threshold_ratio = threshold_ratio
        self._compactor = MicroCompact()
        self.compaction_count = 0

    @property
    def threshold_tokens(self) -> int:
        return int(self.max_context_tokens * self.threshold_ratio)

    def should_compact(self, messages: list[Message]) -> bool:
        """Check if compaction is needed."""
        return estimate_conversation_tokens(messages) > self.threshold_tokens

    def maybe_compact(self, messages: list[Message]) -> list[Message]:
        """Compact if threshold is exceeded, otherwise return as-is."""
        if not self.should_compact(messages):
            return messages

        target = int(self.max_context_tokens * 0.5)  # Compact to 50%
        result = self._compactor.compact(messages, target)
        self.compaction_count += 1
        return result

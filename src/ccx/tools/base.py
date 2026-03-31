"""Base tool protocol and types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ToolContext:
    """Execution context passed to tools."""

    working_dir: Path = field(default_factory=Path.cwd)
    timeout_ms: int = 120_000
    allowed_paths: list[Path] = field(default_factory=list)


@dataclass
class ToolResult:
    """Result of a tool execution."""

    output: str
    is_error: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class Tool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""

    @abstractmethod
    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute the tool with given parameters."""

    def to_api_schema(self) -> dict[str, Any]:
        """Convert to Claude API tool definition format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

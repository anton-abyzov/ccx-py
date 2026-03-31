"""Tool registry for discovering and executing tools."""

from __future__ import annotations

from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not registered."""


class ToolRegistry:
    """Registry that holds and dispatches tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool by its name."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Get a tool by name, raising if not found."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return self._tools[name]

    def list_tools(self) -> list[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def to_api_schemas(self) -> list[dict[str, Any]]:
        """Convert all tools to API schema format."""
        return [t.to_api_schema() for t in self._tools.values()]

    async def execute(
        self, name: str, params: dict[str, Any], ctx: ToolContext
    ) -> ToolResult:
        """Look up and execute a tool by name."""
        tool = self.get(name)
        return await tool.execute(params, ctx)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

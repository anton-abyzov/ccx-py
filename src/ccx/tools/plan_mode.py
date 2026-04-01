"""Plan mode tools: enter and exit read-only planning mode."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

PLAN_MODE_MARKER = Path.home() / ".claude" / ".plan_mode"


class EnterPlanModeTool(Tool):
    @property
    def name(self) -> str:
        return "enter_plan_mode"

    @property
    def description(self) -> str:
        return "Set read-only planning mode. Tools that modify files will be blocked."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        try:
            PLAN_MODE_MARKER.parent.mkdir(parents=True, exist_ok=True)
            PLAN_MODE_MARKER.touch()
        except OSError as e:
            return ToolResult(
                output=f"Failed to enter plan mode: {e}", is_error=True
            )
        return ToolResult(output="Plan mode enabled. File modifications are blocked.")


class ExitPlanModeTool(Tool):
    @property
    def name(self) -> str:
        return "exit_plan_mode"

    @property
    def description(self) -> str:
        return "Exit planning mode and allow file modifications."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        try:
            if PLAN_MODE_MARKER.exists():
                PLAN_MODE_MARKER.unlink()
        except OSError as e:
            return ToolResult(
                output=f"Failed to exit plan mode: {e}", is_error=True
            )
        return ToolResult(output="Plan mode disabled. File modifications are allowed.")

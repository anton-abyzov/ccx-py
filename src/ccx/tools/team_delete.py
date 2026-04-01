"""Team delete tool: remove a team and its task directory."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

TEAMS_ROOT = Path.home() / ".claude" / "teams"
TASKS_ROOT = Path.home() / ".claude" / "tasks"


class TeamDeleteTool(Tool):
    @property
    def name(self) -> str:
        return "team_delete"

    @property
    def description(self) -> str:
        return "Remove a team and its task directory."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "Name of the team to delete.",
                },
            },
            "required": ["team_name"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        team_name = params["team_name"]

        team_dir = TEAMS_ROOT / team_name
        task_dir = TASKS_ROOT / team_name

        if not team_dir.exists() and not task_dir.exists():
            return ToolResult(
                output=f"Team '{team_name}' not found.", is_error=True
            )

        try:
            if team_dir.exists():
                shutil.rmtree(team_dir)
            if task_dir.exists():
                shutil.rmtree(task_dir)
        except OSError as e:
            return ToolResult(output=f"Failed to delete team: {e}", is_error=True)

        return ToolResult(output=f"Deleted team '{team_name}'.")

"""Team create tool: create a named team for multi-agent coordination."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

TEAMS_ROOT = Path.home() / ".claude" / "teams"
TASKS_ROOT = Path.home() / ".claude" / "tasks"


class TeamCreateTool(Tool):
    @property
    def name(self) -> str:
        return "team_create"

    @property
    def description(self) -> str:
        return "Create a named team with task directory for multi-agent coordination."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "Name of the team to create.",
                },
                "description": {
                    "type": "string",
                    "description": "Description of the team's purpose.",
                },
            },
            "required": ["team_name", "description"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        team_name = params["team_name"]
        description = params["description"]

        team_dir = TEAMS_ROOT / team_name
        task_dir = TASKS_ROOT / team_name

        try:
            team_dir.mkdir(parents=True, exist_ok=True)
            task_dir.mkdir(parents=True, exist_ok=True)

            config = {
                "name": team_name,
                "description": description,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            (team_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")
        except OSError as e:
            return ToolResult(output=f"Failed to create team: {e}", is_error=True)

        return ToolResult(
            output=f"Created team '{team_name}' at {team_dir}",
            metadata={"team_dir": str(team_dir), "task_dir": str(task_dir)},
        )

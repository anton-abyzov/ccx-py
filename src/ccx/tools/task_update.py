"""Task update tool: update the status of an existing task."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

TASKS_ROOT = Path.home() / ".claude" / "tasks"


class TaskUpdateTool(Tool):
    @property
    def name(self) -> str:
        return "task_update"

    @property
    def description(self) -> str:
        return "Update the status of an existing task."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task ID to update (e.g. task-001).",
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed"],
                    "description": "New status for the task.",
                },
            },
            "required": ["task_id", "status"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        task_id = params["task_id"]
        status = params["status"]

        if not TASKS_ROOT.exists():
            return ToolResult(output="No task directories found.", is_error=True)

        # Search all team task dirs for the task file
        for team_dir in TASKS_ROOT.iterdir():
            if not team_dir.is_dir():
                continue
            task_path = team_dir / f"{task_id}.json"
            if task_path.exists():
                try:
                    task_data = json.loads(task_path.read_text())
                    task_data["status"] = status
                    task_path.write_text(json.dumps(task_data, indent=2) + "\n")
                except (OSError, json.JSONDecodeError) as e:
                    return ToolResult(
                        output=f"Failed to update task: {e}", is_error=True
                    )
                return ToolResult(output=f"Updated {task_id} status to '{status}'.")

        return ToolResult(output=f"Task '{task_id}' not found.", is_error=True)

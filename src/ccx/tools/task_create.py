"""Task create tool: create a task for tracking work progress."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

TASKS_ROOT = Path.home() / ".claude" / "tasks"


class TaskCreateTool(Tool):
    @property
    def name(self) -> str:
        return "task_create"

    @property
    def description(self) -> str:
        return "Create a task for tracking work progress."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Short title for the task.",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed task description.",
                },
            },
            "required": ["subject", "description"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        subject = params["subject"]
        description = params["description"]

        if not TASKS_ROOT.exists():
            return ToolResult(output="No task directories found.", is_error=True)

        team_dirs = [d for d in TASKS_ROOT.iterdir() if d.is_dir()]
        if not team_dirs:
            return ToolResult(output="No task directories found.", is_error=True)

        team_dir = team_dirs[0]

        # Auto-increment task ID
        existing = list(team_dir.glob("task-*.json"))
        next_num = len(existing) + 1
        task_id = f"task-{next_num:03d}"

        task_data = {
            "id": task_id,
            "subject": subject,
            "description": description,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        task_path = team_dir / f"{task_id}.json"

        try:
            task_path.write_text(json.dumps(task_data, indent=2) + "\n")
        except OSError as e:
            return ToolResult(output=f"Failed to create task: {e}", is_error=True)

        return ToolResult(
            output=f"Created {task_id}: {subject}",
            metadata={"task_id": task_id, "path": str(task_path)},
        )

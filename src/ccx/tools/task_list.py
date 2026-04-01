"""Task list tool: list all tasks and their statuses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

TASKS_ROOT = Path.home() / ".claude" / "tasks"


class TaskListTool(Tool):
    @property
    def name(self) -> str:
        return "task_list"

    @property
    def description(self) -> str:
        return "List all tasks and their statuses."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        if not TASKS_ROOT.exists():
            return ToolResult(output="No tasks found.")

        tasks: list[dict[str, str]] = []
        for team_dir in sorted(TASKS_ROOT.iterdir()):
            if not team_dir.is_dir():
                continue
            for task_file in sorted(team_dir.glob("task-*.json")):
                try:
                    data = json.loads(task_file.read_text())
                    tasks.append({
                        "id": data.get("id", task_file.stem),
                        "subject": data.get("subject", ""),
                        "status": data.get("status", "unknown"),
                        "team": team_dir.name,
                    })
                except (OSError, json.JSONDecodeError):
                    continue

        if not tasks:
            return ToolResult(output="No tasks found.")

        lines = [f"  {t['id']}  [{t['status']}]  {t['subject']}" for t in tasks]
        return ToolResult(
            output=f"Tasks ({len(tasks)}):\n" + "\n".join(lines),
            metadata={"count": len(tasks), "tasks": tasks},
        )

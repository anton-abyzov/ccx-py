"""Todo write tool: file-based todo tracking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

TODO_FILENAME = ".ccx-todos.json"


class TodoWriteTool(Tool):
    @property
    def name(self) -> str:
        return "todo_write"

    @property
    def description(self) -> str:
        return "Write and manage a todo list for tracking tasks."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "description": "List of todo items to write.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique todo ID.",
                            },
                            "content": {
                                "type": "string",
                                "description": "Todo description.",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed"],
                                "description": "Todo status.",
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                                "description": "Priority level.",
                            },
                        },
                        "required": ["id", "content", "status"],
                    },
                },
            },
            "required": ["todos"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        todos = params["todos"]
        todo_path = ctx.working_dir / TODO_FILENAME

        try:
            todo_path.write_text(json.dumps(todos, indent=2) + "\n")
        except OSError as e:
            return ToolResult(output=f"Failed to write todos: {e}", is_error=True)

        pending = sum(1 for t in todos if t.get("status") == "pending")
        in_progress = sum(1 for t in todos if t.get("status") == "in_progress")
        completed = sum(1 for t in todos if t.get("status") == "completed")

        return ToolResult(
            output=(
                f"Wrote {len(todos)} todos to {TODO_FILENAME}\n"
                f"  pending: {pending}, in_progress: {in_progress}, completed: {completed}"
            ),
            metadata={"path": str(todo_path), "count": len(todos)},
        )

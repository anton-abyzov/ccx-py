"""File write tool: create or overwrite files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult


class FileWriteTool(Tool):
    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "Write content to a file, creating parent directories as needed."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the file.",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write.",
                },
            },
            "required": ["file_path", "content"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        file_path = Path(params["file_path"])
        content = params["content"]

        if not file_path.is_absolute():
            file_path = ctx.working_dir / file_path

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        except PermissionError:
            return ToolResult(output=f"Permission denied: {file_path}", is_error=True)
        except OSError as e:
            return ToolResult(output=f"Write error: {e}", is_error=True)

        return ToolResult(output=f"Wrote {len(content)} bytes to {file_path}")

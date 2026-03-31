"""File read tool: read file contents with optional line range."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

MAX_LINES = 2000


class FileReadTool(Tool):
    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read a file's contents with optional offset and limit."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the file.",
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start from (0-based).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read.",
                },
            },
            "required": ["file_path"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        file_path = Path(params["file_path"])
        offset = params.get("offset", 0)
        limit = params.get("limit", MAX_LINES)

        if not file_path.is_absolute():
            file_path = ctx.working_dir / file_path

        if not file_path.exists():
            return ToolResult(output=f"File not found: {file_path}", is_error=True)

        if not file_path.is_file():
            return ToolResult(output=f"Not a file: {file_path}", is_error=True)

        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except PermissionError:
            return ToolResult(output=f"Permission denied: {file_path}", is_error=True)

        lines = text.splitlines(keepends=True)
        selected = lines[offset : offset + limit]

        numbered = []
        for i, line in enumerate(selected, start=offset + 1):
            numbered.append(f"{i}\t{line.rstrip()}")

        return ToolResult(output="\n".join(numbered))

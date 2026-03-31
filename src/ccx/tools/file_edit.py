"""File edit tool: exact string replacement in files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult


class FileEditTool(Tool):
    @property
    def name(self) -> str:
        return "file_edit"

    @property
    def description(self) -> str:
        return "Replace exact text in a file. Fails if old_string is not unique."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the file.",
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact text to find.",
                },
                "new_string": {
                    "type": "string",
                    "description": "Replacement text.",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default false).",
                },
            },
            "required": ["file_path", "old_string", "new_string"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        file_path = Path(params["file_path"])
        old_string = params["old_string"]
        new_string = params["new_string"]
        replace_all = params.get("replace_all", False)

        if not file_path.is_absolute():
            file_path = ctx.working_dir / file_path

        if not file_path.exists():
            return ToolResult(output=f"File not found: {file_path}", is_error=True)

        try:
            content = file_path.read_text(encoding="utf-8")
        except PermissionError:
            return ToolResult(output=f"Permission denied: {file_path}", is_error=True)

        count = content.count(old_string)
        if count == 0:
            return ToolResult(output="old_string not found in file.", is_error=True)

        if not replace_all and count > 1:
            return ToolResult(
                output=f"old_string found {count} times. Use replace_all or provide more context.",
                is_error=True,
            )

        if replace_all:
            new_content = content.replace(old_string, new_string)
        else:
            new_content = content.replace(old_string, new_string, 1)

        file_path.write_text(new_content, encoding="utf-8")
        replacements = count if replace_all else 1
        return ToolResult(output=f"Made {replacements} replacement(s) in {file_path}")

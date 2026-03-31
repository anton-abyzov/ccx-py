"""Glob tool: fast file pattern matching."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

MAX_RESULTS = 500


class GlobTool(Tool):
    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return "Find files matching a glob pattern."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g. '**/*.py').",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in.",
                },
            },
            "required": ["pattern"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        pattern = params["pattern"]
        base = Path(params["path"]) if "path" in params else ctx.working_dir

        if not base.exists():
            return ToolResult(output=f"Directory not found: {base}", is_error=True)

        matches = sorted(base.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

        if not matches:
            return ToolResult(output="No files matched the pattern.")

        results = [str(m) for m in matches[:MAX_RESULTS]]
        suffix = f"\n... ({len(matches) - MAX_RESULTS} more)" if len(matches) > MAX_RESULTS else ""

        return ToolResult(output="\n".join(results) + suffix)

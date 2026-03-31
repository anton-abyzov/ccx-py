"""Grep tool: regex content search powered by ripgrep or fallback."""

from __future__ import annotations

import asyncio
import shutil
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

MAX_OUTPUT_LINES = 250


class GrepTool(Tool):
    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return "Search file contents using regex patterns."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for.",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search.",
                },
                "glob": {
                    "type": "string",
                    "description": "File glob filter (e.g. '*.py').",
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Case insensitive search.",
                },
            },
            "required": ["pattern"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        pattern = params["pattern"]
        path = params.get("path", str(ctx.working_dir))
        glob_filter = params.get("glob")
        case_insensitive = params.get("case_insensitive", False)

        rg = shutil.which("rg")
        if rg:
            return await self._rg_search(rg, pattern, path, glob_filter, case_insensitive)
        return await self._fallback_search(pattern, path, glob_filter, case_insensitive)

    async def _rg_search(
        self,
        rg: str,
        pattern: str,
        path: str,
        glob_filter: str | None,
        case_insensitive: bool,
    ) -> ToolResult:
        cmd = [rg, "--no-heading", "-n", "--max-count", "100"]
        if case_insensitive:
            cmd.append("-i")
        if glob_filter:
            cmd.extend(["--glob", glob_filter])
        cmd.extend([pattern, path])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")

        lines = output.splitlines()
        if len(lines) > MAX_OUTPUT_LINES:
            output = "\n".join(lines[:MAX_OUTPUT_LINES]) + f"\n... ({len(lines) - MAX_OUTPUT_LINES} more lines)"

        if proc.returncode == 1:
            return ToolResult(output="No matches found.")
        if proc.returncode != 0:
            return ToolResult(output=stderr.decode(), is_error=True)

        return ToolResult(output=output)

    async def _fallback_search(
        self,
        pattern: str,
        path: str,
        glob_filter: str | None,
        case_insensitive: bool,
    ) -> ToolResult:
        cmd = ["grep", "-rn"]
        if case_insensitive:
            cmd.append("-i")
        if glob_filter:
            cmd.extend(["--include", glob_filter])
        cmd.extend([pattern, path])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")

        lines = output.splitlines()
        if len(lines) > MAX_OUTPUT_LINES:
            output = "\n".join(lines[:MAX_OUTPUT_LINES])

        return ToolResult(output=output if output else "No matches found.")

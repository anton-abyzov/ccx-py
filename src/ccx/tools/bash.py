"""Bash tool: execute shell commands via asyncio subprocess."""

from __future__ import annotations

import asyncio
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

MAX_OUTPUT_BYTES = 512_000


class BashTool(Tool):
    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return "Execute a bash command and return its output."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds (default 120000).",
                },
            },
            "required": ["command"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        command = params["command"]
        timeout_ms = params.get("timeout", ctx.timeout_ms)
        timeout_s = timeout_ms / 1000

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(ctx.working_dir),
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(
                output=f"Command timed out after {timeout_s}s",
                is_error=True,
            )
        except OSError as e:
            return ToolResult(output=f"Failed to execute: {e}", is_error=True)

        output = stdout.decode("utf-8", errors="replace")
        if len(output) > MAX_OUTPUT_BYTES:
            output = output[:MAX_OUTPUT_BYTES] + "\n... (truncated)"

        return ToolResult(
            output=output,
            is_error=proc.returncode != 0,
            metadata={"exit_code": proc.returncode},
        )

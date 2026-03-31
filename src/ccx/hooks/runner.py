"""Hook runner: execute shell hooks before/after tool calls."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HookType(str, Enum):
    PRE_TOOL = "pre_tool"
    POST_TOOL = "post_tool"
    ON_ERROR = "on_error"
    ON_START = "on_start"


@dataclass
class HookResult:
    """Result of running a hook."""

    exit_code: int
    stdout: str
    stderr: str
    blocked: bool = False  # If True, the tool call should be blocked


@dataclass
class HookRunner:
    """Executes configured shell hooks."""

    hooks: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> HookRunner:
        """Create from settings.json hooks section."""
        return cls(hooks=config)

    async def run(
        self,
        hook_type: HookType,
        tool_name: str = "",
        tool_input: dict[str, Any] | None = None,
    ) -> list[HookResult]:
        """Run all hooks matching the given type."""
        results = []
        hook_configs = self.hooks.get(hook_type.value, [])

        for hook_config in hook_configs:
            # Check if hook matches the tool
            matcher = hook_config.get("matcher", {})
            if matcher:
                tool_pattern = matcher.get("tool_name", "*")
                if tool_pattern != "*" and tool_pattern != tool_name:
                    continue

            command = hook_config.get("command", "")
            if not command:
                continue

            result = await self._execute(command, tool_name, tool_input)
            results.append(result)

            if result.blocked:
                break  # Stop processing further hooks

        return results

    async def _execute(
        self,
        command: str,
        tool_name: str,
        tool_input: dict[str, Any] | None,
    ) -> HookResult:
        """Execute a single hook command."""
        import json
        import os

        env = os.environ.copy()
        env["CCX_TOOL_NAME"] = tool_name
        env["CCX_TOOL_INPUT"] = json.dumps(tool_input or {})

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Exit code 2 = block the tool call
            blocked = proc.returncode == 2

            return HookResult(
                exit_code=proc.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
                blocked=blocked,
            )
        except asyncio.TimeoutError:
            return HookResult(
                exit_code=-1,
                stdout="",
                stderr="Hook timed out after 10s",
                blocked=False,
            )
        except OSError as e:
            return HookResult(
                exit_code=-1,
                stdout="",
                stderr=f"Hook execution failed: {e}",
                blocked=False,
            )

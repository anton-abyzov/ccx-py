"""Agent tool: spawn sub-agents with their own query loop."""

from __future__ import annotations

import asyncio
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult


class AgentTool(Tool):
    """Spawn a sub-agent that runs autonomously with a limited tool set."""

    def __init__(self, create_sub_engine: Any = None) -> None:
        self._create_sub_engine = create_sub_engine

    @property
    def name(self) -> str:
        return "agent"

    @property
    def description(self) -> str:
        return (
            "Launch a sub-agent to handle a complex task autonomously. "
            "The agent gets its own conversation loop with a subset of tools."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The task for the sub-agent to perform.",
                },
                "model": {
                    "type": "string",
                    "description": "Model override (default: claude-sonnet-4-6).",
                },
            },
            "required": ["prompt"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        prompt = params["prompt"]
        model = params.get("model", "claude-sonnet-4-6")

        if self._create_sub_engine is None:
            return ToolResult(
                output=f"Agent sub-engine not configured. Prompt: {prompt}",
                is_error=True,
            )

        try:
            from ccx.api.types import TextContent
            from ccx.core.agent import AgentDef, AgentManager

            manager = AgentManager()
            definition = AgentDef(name="sub-agent", prompt=prompt, model=model)

            async def run_fn(defn: AgentDef) -> str:
                engine = await self._create_sub_engine(defn, ctx)
                blocks = await engine.run()
                texts = [b.text for b in blocks if isinstance(b, TextContent)]
                return "\n".join(texts) if texts else "(no text output)"

            result = await manager.spawn(definition, run_fn=run_fn)

            if result.error:
                return ToolResult(output=f"Agent failed: {result.error}", is_error=True)

            return ToolResult(
                output=result.output,
                metadata={"agent_name": result.name, "status": result.status.value},
            )
        except Exception as e:
            return ToolResult(output=f"Agent spawn error: {e}", is_error=True)

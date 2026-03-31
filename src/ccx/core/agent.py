"""Agent system: spawn and manage sub-agents as asyncio tasks."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentDef:
    """Definition for spawning a sub-agent."""

    name: str
    prompt: str
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 8192
    tools: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result of a completed agent."""

    name: str
    status: AgentStatus
    output: str = ""
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentManager:
    """Manages sub-agents as asyncio tasks."""

    def __init__(self) -> None:
        self._agents: dict[str, asyncio.Task[AgentResult]] = {}
        self._results: dict[str, AgentResult] = {}

    async def spawn(
        self, definition: AgentDef, run_fn: Any = None
    ) -> AgentResult:
        """Spawn a sub-agent and await its result.

        Args:
            definition: Agent configuration.
            run_fn: Async callable(AgentDef) -> str. If None, returns a stub.
        """
        if run_fn is None:
            result = AgentResult(
                name=definition.name,
                status=AgentStatus.COMPLETED,
                output=f"Agent '{definition.name}' stub: no run_fn provided.",
            )
            self._results[definition.name] = result
            return result

        task = asyncio.create_task(self._run_agent(definition, run_fn))
        self._agents[definition.name] = task
        result = await task
        self._results[definition.name] = result
        return result

    async def spawn_background(
        self, definition: AgentDef, run_fn: Any = None
    ) -> None:
        """Spawn a sub-agent in the background."""
        if run_fn is None:
            self._results[definition.name] = AgentResult(
                name=definition.name,
                status=AgentStatus.COMPLETED,
                output=f"Agent '{definition.name}' stub.",
            )
            return

        task = asyncio.create_task(self._run_agent(definition, run_fn))
        self._agents[definition.name] = task

    async def _run_agent(
        self, definition: AgentDef, run_fn: Any
    ) -> AgentResult:
        try:
            output = await run_fn(definition)
            return AgentResult(
                name=definition.name,
                status=AgentStatus.COMPLETED,
                output=str(output),
            )
        except asyncio.CancelledError:
            return AgentResult(
                name=definition.name,
                status=AgentStatus.CANCELLED,
            )
        except Exception as e:
            return AgentResult(
                name=definition.name,
                status=AgentStatus.FAILED,
                error=str(e),
            )

    def get_status(self, name: str) -> AgentStatus:
        if name in self._results:
            return self._results[name].status
        if name in self._agents:
            task = self._agents[name]
            if task.done():
                return AgentStatus.COMPLETED
            return AgentStatus.RUNNING
        return AgentStatus.PENDING

    async def cancel(self, name: str) -> bool:
        if name in self._agents:
            task = self._agents[name]
            if not task.done():
                task.cancel()
                return True
        return False

    @property
    def running_count(self) -> int:
        return sum(1 for t in self._agents.values() if not t.done())

"""Core engine: query loop, agent spawning, context management."""

from ccx.core.agent import AgentDef, AgentManager, AgentResult
from ccx.core.context import SessionContext
from ccx.core.query import QueryEngine

__all__ = ["AgentDef", "AgentManager", "AgentResult", "QueryEngine", "SessionContext"]

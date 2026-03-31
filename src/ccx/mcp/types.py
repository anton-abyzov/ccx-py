"""MCP protocol types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MCPRequest(BaseModel):
    """JSON-RPC 2.0 request for MCP."""

    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: dict[str, Any] = Field(default_factory=dict)


class MCPResponse(BaseModel):
    """JSON-RPC 2.0 response from MCP."""

    jsonrpc: str = "2.0"
    id: int | str | None = None
    result: Any | None = None
    error: MCPError | None = None


class MCPError(BaseModel):
    """JSON-RPC error object."""

    code: int
    message: str
    data: Any | None = None


class MCPTool(BaseModel):
    """Tool definition from an MCP server."""

    name: str
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)


class MCPServerConfig(BaseModel):
    """Configuration for connecting to an MCP server."""

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

"""MCP client: JSON-RPC over stdio to MCP servers."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from ccx.mcp.types import MCPRequest, MCPResponse, MCPServerConfig, MCPTool


class MCPClient:
    """Client that communicates with MCP servers over stdio JSON-RPC."""

    def __init__(self, config: MCPServerConfig) -> None:
        self.config = config
        self._process: asyncio.subprocess.Process | None = None
        self._next_id = 1
        self._pending: dict[int, asyncio.Future[MCPResponse]] = {}

    async def start(self) -> None:
        """Start the MCP server subprocess."""
        env = dict(self.config.env) if self.config.env else None
        self._process = await asyncio.create_subprocess_exec(
            self.config.command,
            *self.config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        # Start reading responses
        asyncio.create_task(self._read_loop())

    async def stop(self) -> None:
        """Stop the MCP server subprocess."""
        if self._process:
            self._process.terminate()
            await self._process.wait()
            self._process = None

    async def _read_loop(self) -> None:
        """Read JSON-RPC responses from the server's stdout."""
        if not self._process or not self._process.stdout:
            return

        buffer = ""
        while True:
            try:
                line = await self._process.stdout.readline()
                if not line:
                    break
                buffer += line.decode("utf-8")

                # Try to parse complete JSON objects
                try:
                    data = json.loads(buffer)
                    buffer = ""
                    response = MCPResponse.model_validate(data)
                    if response.id is not None and isinstance(response.id, int):
                        future = self._pending.pop(response.id, None)
                        if future and not future.done():
                            future.set_result(response)
                except json.JSONDecodeError:
                    continue
            except asyncio.CancelledError:
                break

    async def send(self, method: str, params: dict[str, Any] | None = None) -> MCPResponse:
        """Send a JSON-RPC request and wait for the response."""
        if not self._process or not self._process.stdin:
            raise RuntimeError("MCP server not started")

        request_id = self._next_id
        self._next_id += 1

        request = MCPRequest(
            id=request_id,
            method=method,
            params=params or {},
        )

        future: asyncio.Future[MCPResponse] = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future

        data = request.model_dump_json() + "\n"
        self._process.stdin.write(data.encode("utf-8"))
        await self._process.stdin.drain()

        try:
            return await asyncio.wait_for(future, timeout=30.0)
        except asyncio.TimeoutError:
            self._pending.pop(request_id, None)
            raise

    async def list_tools(self) -> list[MCPTool]:
        """Request the list of available tools from the server."""
        response = await self.send("tools/list")
        if response.error:
            raise RuntimeError(f"MCP error: {response.error.message}")

        tools = []
        if isinstance(response.result, dict):
            for tool_data in response.result.get("tools", []):
                tools.append(MCPTool.model_validate(tool_data))
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        response = await self.send("tools/call", {"name": name, "arguments": arguments})
        if response.error:
            raise RuntimeError(f"MCP tool error: {response.error.message}")
        return response.result

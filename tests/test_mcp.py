"""Tests for MCP types and client."""

import pytest

from ccx.mcp.types import MCPError, MCPRequest, MCPResponse, MCPServerConfig, MCPTool


class TestMCPTypes:
    def test_mcp_request(self):
        req = MCPRequest(id=1, method="tools/list")
        assert req.jsonrpc == "2.0"
        assert req.id == 1
        assert req.method == "tools/list"
        assert req.params == {}

    def test_mcp_request_with_params(self):
        req = MCPRequest(id=2, method="tools/call", params={"name": "bash"})
        assert req.params["name"] == "bash"

    def test_mcp_response_success(self):
        resp = MCPResponse(id=1, result={"tools": []})
        assert resp.error is None
        assert resp.result == {"tools": []}

    def test_mcp_response_error(self):
        resp = MCPResponse(
            id=1,
            error=MCPError(code=-32600, message="Invalid request"),
        )
        assert resp.error is not None
        assert resp.error.code == -32600

    def test_mcp_tool(self):
        tool = MCPTool(
            name="test_tool",
            description="A test",
            input_schema={"type": "object"},
        )
        assert tool.name == "test_tool"

    def test_mcp_server_config(self):
        config = MCPServerConfig(
            command="node",
            args=["server.js"],
            env={"PORT": "3000"},
        )
        assert config.command == "node"
        assert config.args == ["server.js"]
        assert config.env["PORT"] == "3000"

    def test_mcp_server_config_defaults(self):
        config = MCPServerConfig(command="python")
        assert config.args == []
        assert config.env == {}

    def test_mcp_error(self):
        err = MCPError(code=-1, message="fail", data={"detail": "x"})
        assert err.code == -1
        assert err.data == {"detail": "x"}


class TestMCPRequestSerialization:
    def test_request_to_json(self):
        req = MCPRequest(id=1, method="tools/list")
        data = req.model_dump()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert data["method"] == "tools/list"

    def test_response_from_dict(self):
        data = {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}
        resp = MCPResponse.model_validate(data)
        assert resp.id == 1
        assert resp.result == {"tools": []}

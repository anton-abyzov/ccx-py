"""Tests for the tool registry."""

import pytest

from ccx.tools.registry import ToolRegistry, ToolNotFoundError
from ccx.tools.bash import BashTool
from ccx.tools.file_read import FileReadTool


def test_register_and_get():
    reg = ToolRegistry()
    bash = BashTool()
    reg.register(bash)
    assert reg.get("bash") is bash


def test_get_not_found():
    reg = ToolRegistry()
    with pytest.raises(ToolNotFoundError, match="nonexistent"):
        reg.get("nonexistent")


def test_list_tools():
    reg = ToolRegistry()
    reg.register(BashTool())
    reg.register(FileReadTool())
    tools = reg.list_tools()
    assert len(tools) == 2
    names = {t.name for t in tools}
    assert "bash" in names
    assert "file_read" in names


def test_contains():
    reg = ToolRegistry()
    reg.register(BashTool())
    assert "bash" in reg
    assert "missing" not in reg


def test_len():
    reg = ToolRegistry()
    assert len(reg) == 0
    reg.register(BashTool())
    assert len(reg) == 1


def test_to_api_schemas():
    reg = ToolRegistry()
    reg.register(BashTool())
    schemas = reg.to_api_schemas()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "bash"
    assert "input_schema" in schemas[0]
    assert "description" in schemas[0]


@pytest.mark.asyncio
async def test_execute_via_registry(registry, tool_context):
    result = await registry.execute("bash", {"command": "echo test"}, tool_context)
    assert not result.is_error
    assert "test" in result.output


@pytest.mark.asyncio
async def test_execute_not_found(registry, tool_context):
    with pytest.raises(ToolNotFoundError):
        await registry.execute("nonexistent", {}, tool_context)

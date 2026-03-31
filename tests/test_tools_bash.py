"""Tests for the bash tool."""

import pytest

from ccx.tools.bash import BashTool
from ccx.tools.base import ToolContext


@pytest.fixture
def bash_tool():
    return BashTool()


def test_bash_tool_properties(bash_tool):
    assert bash_tool.name == "bash"
    assert "bash" in bash_tool.description.lower()
    assert bash_tool.input_schema["required"] == ["command"]


@pytest.mark.asyncio
async def test_bash_echo(bash_tool, tool_context):
    result = await bash_tool.execute({"command": "echo hello"}, tool_context)
    assert not result.is_error
    assert "hello" in result.output


@pytest.mark.asyncio
async def test_bash_exit_code(bash_tool, tool_context):
    result = await bash_tool.execute({"command": "exit 1"}, tool_context)
    assert result.is_error
    assert result.metadata["exit_code"] == 1


@pytest.mark.asyncio
async def test_bash_working_dir(bash_tool, tool_context):
    result = await bash_tool.execute({"command": "pwd"}, tool_context)
    assert not result.is_error
    assert str(tool_context.working_dir) in result.output


@pytest.mark.asyncio
async def test_bash_timeout(bash_tool, tool_context):
    result = await bash_tool.execute(
        {"command": "sleep 10", "timeout": 500},  # 500ms
        tool_context,
    )
    assert result.is_error
    assert "timed out" in result.output.lower()


@pytest.mark.asyncio
async def test_bash_multiline(bash_tool, tool_context):
    result = await bash_tool.execute(
        {"command": "echo line1 && echo line2"},
        tool_context,
    )
    assert "line1" in result.output
    assert "line2" in result.output


@pytest.mark.asyncio
async def test_bash_api_schema(bash_tool):
    schema = bash_tool.to_api_schema()
    assert schema["name"] == "bash"
    assert "input_schema" in schema

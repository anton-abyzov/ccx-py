"""Tests for the Agent tool."""

import pytest

from ccx.tools.agent_tool import AgentTool
from ccx.tools.base import ToolContext


@pytest.fixture
def agent_tool():
    return AgentTool()


@pytest.mark.asyncio
async def test_agent_tool_properties(agent_tool):
    assert agent_tool.name == "agent"
    assert "sub-agent" in agent_tool.description
    assert agent_tool.input_schema["required"] == ["prompt"]


@pytest.mark.asyncio
async def test_agent_no_engine(agent_tool, tool_context):
    result = await agent_tool.execute({"prompt": "test task"}, tool_context)
    assert result.is_error
    assert "not configured" in result.output


@pytest.mark.asyncio
async def test_agent_with_engine(tool_context):
    async def create_sub(defn, ctx):
        class FakeEngine:
            async def run(self):
                from ccx.api.types import TextContent

                return [TextContent(text=f"Result for: {defn.prompt}")]

        return FakeEngine()

    tool = AgentTool(create_sub_engine=create_sub)
    result = await tool.execute({"prompt": "do something"}, tool_context)
    assert not result.is_error
    assert "Result for: do something" in result.output
    assert result.metadata["status"] == "completed"


@pytest.mark.asyncio
async def test_agent_engine_failure(tool_context):
    async def failing_engine(defn, ctx):
        raise RuntimeError("engine broke")

    tool = AgentTool(create_sub_engine=failing_engine)
    result = await tool.execute({"prompt": "fail"}, tool_context)
    assert result.is_error
    assert "failed" in result.output.lower()


@pytest.mark.asyncio
async def test_agent_model_override(tool_context):
    captured_model = None

    async def capture_engine(defn, ctx):
        nonlocal captured_model
        captured_model = defn.model

        class FakeEngine:
            async def run(self):
                from ccx.api.types import TextContent

                return [TextContent(text="ok")]

        return FakeEngine()

    tool = AgentTool(create_sub_engine=capture_engine)
    await tool.execute(
        {"prompt": "test", "model": "claude-opus-4-6"}, tool_context
    )
    assert captured_model == "claude-opus-4-6"


@pytest.mark.asyncio
async def test_agent_api_schema(agent_tool):
    schema = agent_tool.to_api_schema()
    assert schema["name"] == "agent"
    assert "prompt" in schema["input_schema"]["properties"]

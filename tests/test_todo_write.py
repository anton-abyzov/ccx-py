"""Tests for the TodoWrite tool."""

import json

import pytest

from ccx.tools.todo_write import TodoWriteTool, TODO_FILENAME
from ccx.tools.base import ToolContext


@pytest.fixture
def todo_tool():
    return TodoWriteTool()


def test_tool_properties(todo_tool):
    assert todo_tool.name == "todo_write"
    assert todo_tool.input_schema["required"] == ["todos"]


@pytest.mark.asyncio
async def test_write_todos(todo_tool, tool_context):
    todos = [
        {"id": "1", "content": "Fix bug", "status": "pending"},
        {"id": "2", "content": "Write tests", "status": "completed"},
    ]
    result = await todo_tool.execute({"todos": todos}, tool_context)
    assert not result.is_error
    assert "2 todos" in result.output
    assert "pending: 1" in result.output
    assert "completed: 1" in result.output

    # Verify file
    path = tool_context.working_dir / TODO_FILENAME
    assert path.exists()
    saved = json.loads(path.read_text())
    assert len(saved) == 2
    assert saved[0]["content"] == "Fix bug"


@pytest.mark.asyncio
async def test_write_empty_todos(todo_tool, tool_context):
    result = await todo_tool.execute({"todos": []}, tool_context)
    assert not result.is_error
    assert "0 todos" in result.output


@pytest.mark.asyncio
async def test_write_with_priority(todo_tool, tool_context):
    todos = [
        {"id": "1", "content": "Urgent", "status": "in_progress", "priority": "high"},
    ]
    result = await todo_tool.execute({"todos": todos}, tool_context)
    assert not result.is_error
    assert "in_progress: 1" in result.output


@pytest.mark.asyncio
async def test_overwrite_existing(todo_tool, tool_context):
    # Write first set
    await todo_tool.execute(
        {"todos": [{"id": "1", "content": "old", "status": "pending"}]},
        tool_context,
    )
    # Overwrite
    await todo_tool.execute(
        {"todos": [{"id": "2", "content": "new", "status": "completed"}]},
        tool_context,
    )
    path = tool_context.working_dir / TODO_FILENAME
    saved = json.loads(path.read_text())
    assert len(saved) == 1
    assert saved[0]["content"] == "new"


@pytest.mark.asyncio
async def test_api_schema(todo_tool):
    schema = todo_tool.to_api_schema()
    assert schema["name"] == "todo_write"
    items_schema = schema["input_schema"]["properties"]["todos"]["items"]
    assert "id" in items_schema["properties"]
    assert "content" in items_schema["properties"]
    assert "status" in items_schema["properties"]

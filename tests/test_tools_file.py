"""Tests for file tools (read, write, edit)."""

import pytest
from pathlib import Path

from ccx.tools.file_read import FileReadTool
from ccx.tools.file_write import FileWriteTool
from ccx.tools.file_edit import FileEditTool
from ccx.tools.base import ToolContext


@pytest.fixture
def read_tool():
    return FileReadTool()


@pytest.fixture
def write_tool():
    return FileWriteTool()


@pytest.fixture
def edit_tool():
    return FileEditTool()


@pytest.mark.asyncio
async def test_write_and_read(write_tool, read_tool, tool_context):
    path = str(tool_context.working_dir / "test.txt")

    # Write
    result = await write_tool.execute(
        {"file_path": path, "content": "hello\nworld\n"},
        tool_context,
    )
    assert not result.is_error

    # Read
    result = await read_tool.execute({"file_path": path}, tool_context)
    assert not result.is_error
    assert "hello" in result.output
    assert "world" in result.output


@pytest.mark.asyncio
async def test_read_nonexistent(read_tool, tool_context):
    result = await read_tool.execute(
        {"file_path": "/nonexistent/file.txt"},
        tool_context,
    )
    assert result.is_error
    assert "not found" in result.output.lower()


@pytest.mark.asyncio
async def test_read_with_offset_limit(write_tool, read_tool, tool_context):
    path = str(tool_context.working_dir / "lines.txt")
    content = "\n".join(f"line {i}" for i in range(10))
    await write_tool.execute({"file_path": path, "content": content}, tool_context)

    result = await read_tool.execute(
        {"file_path": path, "offset": 2, "limit": 3},
        tool_context,
    )
    assert not result.is_error
    assert "line 2" in result.output
    assert "line 4" in result.output


@pytest.mark.asyncio
async def test_write_creates_dirs(write_tool, tool_context):
    path = str(tool_context.working_dir / "deep" / "nested" / "file.txt")
    result = await write_tool.execute(
        {"file_path": path, "content": "deep"},
        tool_context,
    )
    assert not result.is_error
    assert Path(path).exists()


@pytest.mark.asyncio
async def test_edit_replace(write_tool, edit_tool, tool_context):
    path = str(tool_context.working_dir / "edit.txt")
    await write_tool.execute(
        {"file_path": path, "content": "foo bar baz"},
        tool_context,
    )

    result = await edit_tool.execute(
        {"file_path": path, "old_string": "bar", "new_string": "qux"},
        tool_context,
    )
    assert not result.is_error

    content = Path(path).read_text()
    assert "qux" in content
    assert "bar" not in content


@pytest.mark.asyncio
async def test_edit_not_found(edit_tool, tool_context):
    path = str(tool_context.working_dir / "missing.txt")
    result = await edit_tool.execute(
        {"file_path": path, "old_string": "a", "new_string": "b"},
        tool_context,
    )
    assert result.is_error


@pytest.mark.asyncio
async def test_edit_ambiguous(write_tool, edit_tool, tool_context):
    path = str(tool_context.working_dir / "dup.txt")
    await write_tool.execute(
        {"file_path": path, "content": "aaa aaa"},
        tool_context,
    )

    result = await edit_tool.execute(
        {"file_path": path, "old_string": "aaa", "new_string": "bbb"},
        tool_context,
    )
    assert result.is_error
    assert "2 times" in result.output


@pytest.mark.asyncio
async def test_edit_replace_all(write_tool, edit_tool, tool_context):
    path = str(tool_context.working_dir / "all.txt")
    await write_tool.execute(
        {"file_path": path, "content": "aaa aaa aaa"},
        tool_context,
    )

    result = await edit_tool.execute(
        {"file_path": path, "old_string": "aaa", "new_string": "bbb", "replace_all": True},
        tool_context,
    )
    assert not result.is_error
    assert "3 replacement" in result.output

    content = Path(path).read_text()
    assert content == "bbb bbb bbb"

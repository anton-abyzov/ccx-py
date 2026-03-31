"""Tests for glob and grep tools."""

import pytest
from pathlib import Path

from ccx.tools.glob_tool import GlobTool
from ccx.tools.grep import GrepTool
from ccx.tools.base import ToolContext


@pytest.fixture
def glob_tool():
    return GlobTool()


@pytest.fixture
def grep_tool():
    return GrepTool()


@pytest.fixture
def search_dir(tmp_path: Path) -> Path:
    """Create a directory with some files for searching."""
    (tmp_path / "a.py").write_text("def hello():\n    print('hello')\n")
    (tmp_path / "b.py").write_text("def world():\n    return 42\n")
    (tmp_path / "c.txt").write_text("not python\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "d.py").write_text("import os\n")
    return tmp_path


@pytest.mark.asyncio
async def test_glob_py_files(glob_tool, search_dir):
    ctx = ToolContext(working_dir=search_dir)
    result = await glob_tool.execute({"pattern": "**/*.py"}, ctx)
    assert not result.is_error
    assert "a.py" in result.output
    assert "b.py" in result.output
    assert "d.py" in result.output


@pytest.mark.asyncio
async def test_glob_no_matches(glob_tool, search_dir):
    ctx = ToolContext(working_dir=search_dir)
    result = await glob_tool.execute({"pattern": "**/*.rs"}, ctx)
    assert "No files" in result.output


@pytest.mark.asyncio
async def test_glob_specific_dir(glob_tool, search_dir):
    ctx = ToolContext(working_dir=search_dir)
    result = await glob_tool.execute(
        {"pattern": "*.py", "path": str(search_dir / "sub")},
        ctx,
    )
    assert "d.py" in result.output
    assert "a.py" not in result.output


@pytest.mark.asyncio
async def test_grep_pattern(grep_tool, search_dir):
    ctx = ToolContext(working_dir=search_dir)
    result = await grep_tool.execute(
        {"pattern": "def", "path": str(search_dir)},
        ctx,
    )
    assert not result.is_error
    assert "hello" in result.output


@pytest.mark.asyncio
async def test_grep_no_match(grep_tool, search_dir):
    ctx = ToolContext(working_dir=search_dir)
    result = await grep_tool.execute(
        {"pattern": "nonexistent_string", "path": str(search_dir)},
        ctx,
    )
    assert "No matches" in result.output or result.output.strip() == ""


@pytest.mark.asyncio
async def test_grep_case_insensitive(grep_tool, search_dir):
    ctx = ToolContext(working_dir=search_dir)
    result = await grep_tool.execute(
        {"pattern": "DEF", "path": str(search_dir), "case_insensitive": True},
        ctx,
    )
    assert "hello" in result.output or "def" in result.output.lower()


@pytest.mark.asyncio
async def test_glob_tool_properties(glob_tool):
    assert glob_tool.name == "glob"
    assert glob_tool.input_schema["required"] == ["pattern"]


@pytest.mark.asyncio
async def test_grep_tool_properties(grep_tool):
    assert grep_tool.name == "grep"
    assert grep_tool.input_schema["required"] == ["pattern"]

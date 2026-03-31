"""Tests for the NotebookEdit tool."""

import json

import pytest

from ccx.tools.notebook_edit import NotebookEditTool, _to_source_lines, _new_notebook
from ccx.tools.base import ToolContext


@pytest.fixture
def nb_tool():
    return NotebookEditTool()


@pytest.fixture
def sample_notebook(tmp_path):
    """Create a sample .ipynb file."""
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": [
            {
                "cell_type": "code",
                "source": ["print('hello')\n"],
                "metadata": {},
                "outputs": [{"text": "hello\n"}],
                "execution_count": 1,
            },
            {
                "cell_type": "markdown",
                "source": ["# Title\n"],
                "metadata": {},
            },
        ],
    }
    path = tmp_path / "test.ipynb"
    path.write_text(json.dumps(nb))
    return path


def test_tool_properties(nb_tool):
    assert nb_tool.name == "notebook_edit"
    assert nb_tool.input_schema["required"] == ["path"]


def test_to_source_lines():
    assert _to_source_lines("a\nb\nc") == ["a\n", "b\n", "c"]
    assert _to_source_lines("single") == ["single"]
    assert _to_source_lines("a\n") == ["a\n"]


def test_new_notebook():
    nb = _new_notebook()
    assert nb["nbformat"] == 4
    assert nb["cells"] == []


@pytest.mark.asyncio
async def test_replace_cell(nb_tool, sample_notebook):
    ctx = ToolContext(working_dir=sample_notebook.parent)
    result = await nb_tool.execute(
        {
            "path": str(sample_notebook),
            "cell_index": 0,
            "new_source": "print('world')",
            "operation": "replace",
        },
        ctx,
    )
    assert not result.is_error
    assert "Replaced cell 0" in result.output

    nb = json.loads(sample_notebook.read_text())
    assert nb["cells"][0]["source"] == ["print('world')"]
    # Code cell outputs should be cleared
    assert nb["cells"][0]["outputs"] == []
    assert nb["cells"][0]["execution_count"] is None


@pytest.mark.asyncio
async def test_insert_cell(nb_tool, sample_notebook):
    ctx = ToolContext(working_dir=sample_notebook.parent)
    result = await nb_tool.execute(
        {
            "path": str(sample_notebook),
            "cell_index": 1,
            "new_source": "# New Section",
            "cell_type": "markdown",
            "operation": "insert",
        },
        ctx,
    )
    assert not result.is_error
    assert "Inserted markdown cell at index 1" in result.output

    nb = json.loads(sample_notebook.read_text())
    assert len(nb["cells"]) == 3
    assert nb["cells"][1]["cell_type"] == "markdown"


@pytest.mark.asyncio
async def test_delete_cell(nb_tool, sample_notebook):
    ctx = ToolContext(working_dir=sample_notebook.parent)
    result = await nb_tool.execute(
        {
            "path": str(sample_notebook),
            "cell_index": 1,
            "operation": "delete",
        },
        ctx,
    )
    assert not result.is_error
    assert "Deleted cell 1" in result.output

    nb = json.loads(sample_notebook.read_text())
    assert len(nb["cells"]) == 1


@pytest.mark.asyncio
async def test_replace_out_of_range(nb_tool, sample_notebook):
    ctx = ToolContext(working_dir=sample_notebook.parent)
    result = await nb_tool.execute(
        {
            "path": str(sample_notebook),
            "cell_index": 99,
            "new_source": "x",
            "operation": "replace",
        },
        ctx,
    )
    assert result.is_error
    assert "out of range" in result.output


@pytest.mark.asyncio
async def test_nonexistent_file(nb_tool, tool_context):
    result = await nb_tool.execute(
        {"path": "/nonexistent/nb.ipynb", "operation": "replace"},
        tool_context,
    )
    assert result.is_error
    assert "not found" in result.output


@pytest.mark.asyncio
async def test_insert_creates_new_notebook(nb_tool, tmp_path):
    ctx = ToolContext(working_dir=tmp_path)
    path = tmp_path / "new.ipynb"
    result = await nb_tool.execute(
        {
            "path": str(path),
            "new_source": "x = 1",
            "cell_type": "code",
            "operation": "insert",
        },
        ctx,
    )
    assert not result.is_error
    assert path.exists()
    nb = json.loads(path.read_text())
    assert len(nb["cells"]) == 1
    assert nb["cells"][0]["cell_type"] == "code"


@pytest.mark.asyncio
async def test_relative_path(nb_tool, sample_notebook):
    ctx = ToolContext(working_dir=sample_notebook.parent)
    result = await nb_tool.execute(
        {
            "path": "test.ipynb",
            "cell_index": 0,
            "new_source": "x = 42",
            "operation": "replace",
        },
        ctx,
    )
    assert not result.is_error


@pytest.mark.asyncio
async def test_api_schema(nb_tool):
    schema = nb_tool.to_api_schema()
    assert schema["name"] == "notebook_edit"
    props = schema["input_schema"]["properties"]
    assert "path" in props
    assert "cell_index" in props
    assert "operation" in props

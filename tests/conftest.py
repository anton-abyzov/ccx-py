"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccx.tools.base import ToolContext
from ccx.tools.registry import ToolRegistry
from ccx.tools.bash import BashTool
from ccx.tools.file_read import FileReadTool
from ccx.tools.file_write import FileWriteTool
from ccx.tools.file_edit import FileEditTool
from ccx.tools.glob_tool import GlobTool
from ccx.tools.grep import GrepTool


@pytest.fixture
def tmp_working_dir(tmp_path: Path) -> Path:
    """Provide a temporary working directory."""
    return tmp_path


@pytest.fixture
def tool_context(tmp_working_dir: Path) -> ToolContext:
    """Provide a ToolContext rooted in a temp dir."""
    return ToolContext(working_dir=tmp_working_dir)


@pytest.fixture
def registry() -> ToolRegistry:
    """Provide a fully-loaded tool registry."""
    reg = ToolRegistry()
    reg.register(BashTool())
    reg.register(FileReadTool())
    reg.register(FileWriteTool())
    reg.register(FileEditTool())
    reg.register(GlobTool())
    reg.register(GrepTool())
    return reg

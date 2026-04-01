"""Tests for the system prompt builder."""

from pathlib import Path

from ccx.core.prompt import build_system_prompt
from ccx.tools.bash import BashTool
from ccx.tools.file_read import FileReadTool


def test_build_basic_prompt():
    prompt = build_system_prompt(tools=[], working_dir=Path("/tmp"))
    assert "AI coding assistant" in prompt
    assert "/tmp" in prompt
    assert "No tools available" in prompt


def test_build_with_tools():
    tools = [BashTool(), FileReadTool()]
    prompt = build_system_prompt(tools=tools, working_dir=Path("/home"))
    assert "bash" in prompt
    assert "file_read" in prompt
    assert "/home" in prompt


def test_build_with_claude_md():
    prompt = build_system_prompt(
        tools=[],
        working_dir=Path("/tmp"),
        claude_md="Always use Python 3.11",
    )
    assert "CLAUDE.md" in prompt
    assert "Always use Python 3.11" in prompt


def test_build_without_claude_md():
    prompt = build_system_prompt(tools=[], working_dir=Path("/tmp"))
    assert "CLAUDE.md" not in prompt


def test_environment_section():
    prompt = build_system_prompt(tools=[], working_dir=Path("/project"))
    assert "Working directory" in prompt
    assert "Platform" in prompt


def test_tools_listed():
    tools = [BashTool(), FileReadTool()]
    prompt = build_system_prompt(tools=tools)
    assert "## bash" in prompt
    assert "## file_read" in prompt
    assert "Input Schema:" in prompt
    assert "```json" in prompt

"""System prompt builder for Claude conversations."""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ccx.tools.base import Tool


def build_system_prompt(
    tools: list[Tool],
    working_dir: Path | None = None,
    claude_md: str = "",
) -> str:
    """Build the system prompt including role, tools, environment, and CLAUDE.md.

    Args:
        tools: List of available tools.
        working_dir: Current working directory.
        claude_md: Merged CLAUDE.md content.
    """
    cwd = str(working_dir or Path.cwd())

    sections = [
        _role_section(),
        _environment_section(cwd),
        _tools_section(tools),
    ]

    if claude_md:
        sections.append(_claude_md_section(claude_md))

    return "\n\n".join(sections)


def _role_section() -> str:
    return (
        "You are an AI coding assistant. You help users with software engineering tasks "
        "including writing code, debugging, refactoring, and explaining code.\n"
        "\n"
        "Guidelines:\n"
        "- Be concise and direct in responses.\n"
        "- Read files before modifying them.\n"
        "- Prefer editing existing files over creating new ones.\n"
        "- Use the appropriate tool for each task.\n"
        "- Do not add unnecessary features or refactoring beyond what was asked."
    )


def _environment_section(cwd: str) -> str:
    return (
        f"# Environment\n"
        f"- Working directory: {cwd}\n"
        f"- Platform: {platform.system().lower()}\n"
        f"- Python: {platform.python_version()}\n"
        f"- Shell: {os.environ.get('SHELL', 'unknown')}"
    )


def _tools_section(tools: list[Tool]) -> str:
    if not tools:
        return "# Tools\nNo tools available."

    lines = ["# Available Tools"]
    for tool in tools:
        lines.append(f"\n## {tool.name}")
        lines.append(tool.description)
        lines.append(f"\nInput Schema:\n```json\n{json.dumps(tool.input_schema, indent=2)}\n```")
    return "\n".join(lines)


def _claude_md_section(claude_md: str) -> str:
    return f"# User Instructions (CLAUDE.md)\n{claude_md}"

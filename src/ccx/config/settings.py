"""Settings loaded from ~/.claude/settings.json and environment."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _default_config_dir() -> Path:
    return Path.home() / ".claude"


@dataclass
class Settings:
    """Application settings merged from config file and environment."""

    api_key: str = ""
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 8192
    permission_mode: str = "default"
    custom_instructions: str = ""
    allowed_tools: list[str] = field(default_factory=list)
    hooks: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_dir: Path | None = None) -> Settings:
        """Load settings from config file and environment variables."""
        config_dir = config_dir or _default_config_dir()
        settings = cls()

        # Load from settings.json
        settings_file = config_dir / "settings.json"
        if settings_file.exists():
            try:
                data = json.loads(settings_file.read_text())
                settings.permission_mode = data.get("permissions", {}).get(
                    "mode", settings.permission_mode
                )
                settings.allowed_tools = data.get("permissions", {}).get(
                    "allow", settings.allowed_tools
                )
                settings.custom_instructions = data.get(
                    "customInstructions", settings.custom_instructions
                )
                settings.hooks = data.get("hooks", settings.hooks)
            except (json.JSONDecodeError, KeyError):
                pass

        # Environment overrides
        settings.api_key = os.environ.get("ANTHROPIC_API_KEY", settings.api_key)
        settings.model = os.environ.get("CCX_MODEL", settings.model)
        if max_tokens_str := os.environ.get("CCX_MAX_TOKENS"):
            try:
                settings.max_tokens = int(max_tokens_str)
            except ValueError:
                pass

        return settings

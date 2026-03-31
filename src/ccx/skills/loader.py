"""Skill loader: discover and parse markdown skill files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Skill:
    """A parsed skill definition."""

    name: str
    description: str = ""
    trigger: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    file_path: Path | None = None


class SkillLoader:
    """Discovers and loads skill markdown files."""

    def __init__(self, skill_dirs: list[Path] | None = None) -> None:
        self.skill_dirs = skill_dirs or [
            Path.home() / ".claude" / "skills",
        ]

    def discover(self) -> list[Skill]:
        """Find all skill files in configured directories."""
        skills = []
        for skill_dir in self.skill_dirs:
            if not skill_dir.exists():
                continue
            for md_file in skill_dir.rglob("*.md"):
                skill = self._parse_skill(md_file)
                if skill:
                    skills.append(skill)
        return skills

    def load(self, name: str) -> Skill | None:
        """Load a specific skill by name."""
        for skill in self.discover():
            if skill.name == name:
                return skill
        return None

    def _parse_skill(self, path: Path) -> Skill | None:
        """Parse a skill markdown file with optional YAML frontmatter."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        metadata: dict[str, Any] = {}
        content = text

        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    pass
                content = parts[2].strip()

        return Skill(
            name=metadata.get("name", path.stem),
            description=metadata.get("description", ""),
            trigger=metadata.get("trigger", ""),
            content=content,
            metadata=metadata,
            file_path=path,
        )

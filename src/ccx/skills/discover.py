"""Discover skills from filesystem: ~/.claude/skills, cwd skills, specweave plugins."""

from __future__ import annotations

from pathlib import Path

import yaml


def discover_all_skills() -> dict[str, str]:
    """Scan filesystem for skill files, return {name: description}."""
    skills: dict[str, str] = {}

    skill_dirs = [
        Path.home() / ".claude" / "skills",
        Path.cwd() / ".claude" / "skills",
    ]

    # Scan specweave plugin dirs under nvm
    nvm_base = Path.home() / ".nvm" / "versions" / "node"
    if nvm_base.exists():
        for ver in nvm_base.iterdir():
            plugins = ver / "lib" / "node_modules" / "specweave" / "plugins"
            if plugins.exists():
                for plugin in plugins.iterdir():
                    skills_dir = plugin / "skills"
                    if skills_dir.exists():
                        _scan_dir(skills_dir, skills)

    for d in skill_dirs:
        if d.exists():
            _scan_dir(d, skills)

    return skills


def _scan_dir(d: Path, skills: dict[str, str]) -> None:
    """Scan a directory for skill .md files and SKILL.md in subdirs."""
    for item in d.iterdir():
        if item.suffix == ".md" and item.is_file():
            name, desc = _parse_frontmatter(item)
            if name:
                skills[name] = desc
        elif item.is_dir():
            skill_file = item / "SKILL.md"
            if skill_file.exists():
                name, desc = _parse_frontmatter(skill_file)
                if name:
                    skills[name] = desc


def _derive_name(path: Path) -> str | None:
    """Derive skill name from file path.

    plugins/specweave/skills/team-lead/SKILL.md → sw:team-lead
    plugins/other-plugin/skills/foo/SKILL.md → other-plugin:foo
    ~/.claude/skills/nanobanana/SKILL.md → nanobanana
    ~/.claude/skills/greeting.md → greeting
    """
    skill_name = path.parent.name if path.name == "SKILL.md" else path.stem
    if not skill_name:
        return None

    parts = path.parts
    try:
        plugins_idx = parts.index("plugins")
        plugin_name = parts[plugins_idx + 1]
        prefix = "sw" if plugin_name == "specweave" else plugin_name
        return f"{prefix}:{skill_name}"
    except (ValueError, IndexError):
        return skill_name


def _parse_frontmatter(path: Path) -> tuple[str | None, str]:
    """Extract description from YAML frontmatter, derive name from path."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return None, ""

    if not content.startswith("---"):
        return None, ""

    try:
        end = content.index("---", 3)
    except ValueError:
        return None, ""

    fm_text = content[3:end]
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return None, ""

    name = _derive_name(path)
    if not name:
        return None, ""

    desc = fm.get("description", name)
    return name, str(desc)

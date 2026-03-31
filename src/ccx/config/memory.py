"""Memory system: persistent file-based memory across sessions."""

from __future__ import annotations

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    """A single memory entry with metadata."""

    name: str
    description: str
    memory_type: str  # user, feedback, project, reference
    content: str
    file_path: Path | None = None


class MemorySystem:
    """File-based memory system stored in ~/.claude/projects/*/memory/."""

    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = memory_dir

    def list_entries(self) -> list[MemoryEntry]:
        """List all memory entries."""
        entries = []
        if not self.memory_dir.exists():
            return entries

        for md_file in sorted(self.memory_dir.glob("*.md")):
            if md_file.name == "MEMORY.md":
                continue
            entry = self._parse_file(md_file)
            if entry:
                entries.append(entry)

        return entries

    def get(self, name: str) -> MemoryEntry | None:
        """Get a memory entry by name."""
        for entry in self.list_entries():
            if entry.name == name:
                return entry
        return None

    def save(self, entry: MemoryEntry) -> Path:
        """Save a memory entry to disk."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        slug = entry.name.lower().replace(" ", "_").replace("-", "_")
        file_path = self.memory_dir / f"{entry.memory_type}_{slug}.md"

        frontmatter = {
            "name": entry.name,
            "description": entry.description,
            "type": entry.memory_type,
        }

        content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{entry.content}\n"
        file_path.write_text(content, encoding="utf-8")
        entry.file_path = file_path

        self._update_index(entry)
        return file_path

    def delete(self, name: str) -> bool:
        """Delete a memory entry by name."""
        entry = self.get(name)
        if entry and entry.file_path and entry.file_path.exists():
            entry.file_path.unlink()
            return True
        return False

    def _parse_file(self, path: Path) -> MemoryEntry | None:
        """Parse a memory markdown file with YAML frontmatter."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        if not text.startswith("---"):
            return None

        parts = text.split("---", 2)
        if len(parts) < 3:
            return None

        try:
            meta: dict[str, Any] = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError:
            return None

        return MemoryEntry(
            name=meta.get("name", path.stem),
            description=meta.get("description", ""),
            memory_type=meta.get("type", "project"),
            content=parts[2].strip(),
            file_path=path,
        )

    def _update_index(self, entry: MemoryEntry) -> None:
        """Update MEMORY.md index with the new entry."""
        index_path = self.memory_dir / "MEMORY.md"

        if index_path.exists():
            index_content = index_path.read_text(encoding="utf-8")
        else:
            index_content = "# Memory Index\n\n"

        slug = entry.name.lower().replace(" ", "_").replace("-", "_")
        filename = f"{entry.memory_type}_{slug}.md"
        line = f"- [{entry.name}]({filename}) — {entry.description}"

        # Check if entry already exists in index
        if filename in index_content:
            # Update existing line
            lines = index_content.splitlines()
            new_lines = []
            for existing_line in lines:
                if filename in existing_line:
                    new_lines.append(line)
                else:
                    new_lines.append(existing_line)
            index_content = "\n".join(new_lines) + "\n"
        else:
            index_content += line + "\n"

        index_path.write_text(index_content, encoding="utf-8")

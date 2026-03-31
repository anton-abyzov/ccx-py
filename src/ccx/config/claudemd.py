"""CLAUDE.md discovery: find and merge instruction files."""

from __future__ import annotations

from pathlib import Path


class ClaudeMdDiscovery:
    """Discovers CLAUDE.md files from project root up to home directory."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path.cwd()

    def discover(self) -> list[Path]:
        """Find all CLAUDE.md files from project dir up to home.

        Returns paths ordered from most specific (project) to most general (home).
        """
        found: list[Path] = []
        home = Path.home()

        # Walk up from project dir
        current = self.project_dir.resolve()
        while current != current.parent:
            candidate = current / "CLAUDE.md"
            if candidate.exists():
                found.append(candidate)
            if current == home:
                break
            current = current.parent

        # Also check ~/.claude/CLAUDE.md
        global_md = home / ".claude" / "CLAUDE.md"
        if global_md.exists() and global_md not in found:
            found.append(global_md)

        return found

    def load_merged(self) -> str:
        """Load and merge all discovered CLAUDE.md files."""
        paths = self.discover()
        if not paths:
            return ""

        sections = []
        for path in reversed(paths):  # Global first, then specific
            try:
                content = path.read_text(encoding="utf-8").strip()
                if content:
                    sections.append(f"# From {path}\n\n{content}")
            except OSError:
                continue

        return "\n\n---\n\n".join(sections)

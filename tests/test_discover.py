"""Tests for skill discovery."""

from pathlib import Path

import pytest

from ccx.skills.discover import _parse_frontmatter, _scan_dir, discover_all_skills


@pytest.fixture
def skill_tree(tmp_path: Path) -> Path:
    """Create a directory tree with various skill files."""
    d = tmp_path / "skills"
    d.mkdir()

    # Normal skill file
    (d / "greeting.md").write_text(
        "---\nname: greeting\ndescription: Greet the user\n---\nSay hello.\n"
    )

    # Skill in subdirectory with SKILL.md
    sub = d / "debug-helper"
    sub.mkdir()
    (sub / "SKILL.md").write_text(
        "---\nname: sw:debug\ndescription: Debug helper skill\n---\nHelp debug.\n"
    )

    # File without frontmatter (should be skipped)
    (d / "plain.md").write_text("No frontmatter here.\n")

    # File with broken frontmatter
    (d / "broken.md").write_text("---\nbad: [yaml: {{\n---\ncontent\n")

    # File without name in frontmatter
    (d / "noname.md").write_text("---\ndescription: orphan\n---\ncontent\n")

    return d


class TestParseFrontmatter:
    def test_valid(self, tmp_path: Path):
        p = tmp_path / "skill.md"
        p.write_text("---\nname: test\ndescription: A test skill\n---\nbody\n")
        name, desc = _parse_frontmatter(p)
        assert name == "test"
        assert desc == "A test skill"

    def test_no_frontmatter(self, tmp_path: Path):
        p = tmp_path / "plain.md"
        p.write_text("Just content.\n")
        name, desc = _parse_frontmatter(p)
        assert name is None

    def test_missing_closing_delimiter(self, tmp_path: Path):
        p = tmp_path / "bad.md"
        p.write_text("---\nname: x\nno closing delimiter")
        name, desc = _parse_frontmatter(p)
        assert name is None

    def test_no_name_field(self, tmp_path: Path):
        p = tmp_path / "noname.md"
        p.write_text("---\ndescription: orphan\n---\ncontent\n")
        name, desc = _parse_frontmatter(p)
        assert name is None

    def test_description_defaults_to_name(self, tmp_path: Path):
        p = tmp_path / "minimal.md"
        p.write_text("---\nname: minimal\n---\ncontent\n")
        name, desc = _parse_frontmatter(p)
        assert name == "minimal"
        assert desc == "minimal"

    def test_unreadable_file(self, tmp_path: Path):
        p = tmp_path / "missing.md"
        name, desc = _parse_frontmatter(p)
        assert name is None

    def test_bad_yaml(self, tmp_path: Path):
        p = tmp_path / "bad.md"
        p.write_text("---\nbad: [yaml: {{\n---\ncontent\n")
        name, desc = _parse_frontmatter(p)
        assert name is None


class TestScanDir:
    def test_finds_md_files(self, skill_tree: Path):
        skills: dict[str, str] = {}
        _scan_dir(skill_tree, skills)
        assert "greeting" in skills
        assert skills["greeting"] == "Greet the user"

    def test_finds_subdir_skills(self, skill_tree: Path):
        skills: dict[str, str] = {}
        _scan_dir(skill_tree, skills)
        assert "sw:debug" in skills

    def test_skips_no_frontmatter(self, skill_tree: Path):
        skills: dict[str, str] = {}
        _scan_dir(skill_tree, skills)
        assert "plain" not in skills

    def test_skips_broken_yaml(self, skill_tree: Path):
        skills: dict[str, str] = {}
        _scan_dir(skill_tree, skills)
        assert "broken" not in skills


class TestDiscoverAllSkills:
    def test_returns_dict(self, monkeypatch, tmp_path: Path):
        empty = tmp_path / "empty"
        empty.mkdir()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.chdir(tmp_path)
        result = discover_all_skills()
        assert isinstance(result, dict)

    def test_finds_home_skills(self, monkeypatch, tmp_path: Path):
        skill_dir = tmp_path / ".claude" / "skills"
        skill_dir.mkdir(parents=True)
        (skill_dir / "my-skill.md").write_text(
            "---\nname: my-skill\ndescription: My custom skill\n---\ncontent\n"
        )
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.chdir(tmp_path)
        result = discover_all_skills()
        assert "my-skill" in result
        assert result["my-skill"] == "My custom skill"

    def test_finds_cwd_skills(self, monkeypatch, tmp_path: Path):
        skill_dir = tmp_path / ".claude" / "skills"
        skill_dir.mkdir(parents=True)
        (skill_dir / "local.md").write_text(
            "---\nname: local-skill\ndescription: Project skill\n---\ncontent\n"
        )
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "fakehome")
        monkeypatch.chdir(tmp_path)
        result = discover_all_skills()
        assert "local-skill" in result

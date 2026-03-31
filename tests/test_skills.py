"""Tests for the skill system."""

import pytest
from pathlib import Path

from ccx.skills.loader import Skill, SkillLoader
from ccx.skills.executor import SkillExecutor


@pytest.fixture
def skill_dir(tmp_path: Path) -> Path:
    """Create a temp directory with skill files."""
    skills = tmp_path / "skills"
    skills.mkdir()

    (skills / "greeting.md").write_text(
        "---\nname: greeting\ndescription: Greet the user\ntrigger: hello\n---\n\nSay hello warmly.\n"
    )
    (skills / "debug.md").write_text(
        "---\nname: debug\ndescription: Debug helper\ntrigger: debug\n---\n\nHelp debug issues.\n"
    )
    (skills / "plain.md").write_text("No frontmatter, just content.\n")

    return skills


@pytest.fixture
def loader(skill_dir: Path) -> SkillLoader:
    return SkillLoader(skill_dirs=[skill_dir])


@pytest.fixture
def executor(loader: SkillLoader) -> SkillExecutor:
    return SkillExecutor(loader)


class TestSkillLoader:
    def test_discover(self, loader):
        skills = loader.discover()
        assert len(skills) == 3
        names = {s.name for s in skills}
        assert "greeting" in names
        assert "debug" in names

    def test_load_by_name(self, loader):
        skill = loader.load("greeting")
        assert skill is not None
        assert skill.name == "greeting"
        assert "hello warmly" in skill.content

    def test_load_missing(self, loader):
        assert loader.load("nonexistent") is None

    def test_load_plain_md(self, loader):
        skill = loader.load("plain")
        assert skill is not None
        assert skill.content.strip() == "No frontmatter, just content."

    def test_empty_dirs(self, tmp_path):
        loader = SkillLoader(skill_dirs=[tmp_path / "empty"])
        assert loader.discover() == []


class TestSkillExecutor:
    def test_activate(self, executor):
        skill = executor.activate("greeting")
        assert skill is not None
        assert len(executor.active_skills) == 1

    def test_activate_missing(self, executor):
        skill = executor.activate("nonexistent")
        assert skill is None
        assert len(executor.active_skills) == 0

    def test_deactivate(self, executor):
        executor.activate("greeting")
        assert executor.deactivate("greeting")
        assert len(executor.active_skills) == 0

    def test_deactivate_missing(self, executor):
        assert not executor.deactivate("nonexistent")

    def test_system_prompt_additions(self, executor):
        executor.activate("greeting")
        additions = executor.get_system_prompt_additions()
        assert '<skill name="greeting">' in additions
        assert "hello warmly" in additions

    def test_empty_additions(self, executor):
        assert executor.get_system_prompt_additions() == ""

    def test_match_trigger(self, executor):
        matches = executor.match_trigger("hello there")
        assert len(matches) == 1
        assert matches[0].name == "greeting"

    def test_no_trigger_match(self, executor):
        matches = executor.match_trigger("something unrelated")
        assert len(matches) == 0

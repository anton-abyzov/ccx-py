"""Tests for configuration modules."""

import json
import pytest
from pathlib import Path

from ccx.config.settings import Settings
from ccx.config.claudemd import ClaudeMdDiscovery
from ccx.config.memory import MemoryEntry, MemorySystem


class TestSettings:
    def test_defaults(self):
        settings = Settings()
        assert settings.model == "claude-sonnet-4-6"
        assert settings.max_tokens == 8192
        assert settings.permission_mode == "default"

    def test_load_from_file(self, tmp_path):
        config_dir = tmp_path / ".claude"
        config_dir.mkdir()
        (config_dir / "settings.json").write_text(
            json.dumps({
                "permissions": {"mode": "bypass", "allow": ["bash"]},
                "customInstructions": "be helpful",
            })
        )
        settings = Settings.load(config_dir)
        assert settings.permission_mode == "bypass"
        assert settings.allowed_tools == ["bash"]
        assert settings.custom_instructions == "be helpful"

    def test_load_missing_file(self, tmp_path):
        settings = Settings.load(tmp_path / "nonexistent")
        assert settings.model == "claude-sonnet-4-6"

    def test_env_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("CCX_MODEL", "claude-opus-4-6")
        monkeypatch.setenv("CCX_MAX_TOKENS", "4096")
        settings = Settings.load(tmp_path)
        assert settings.api_key == "test-key"
        assert settings.model == "claude-opus-4-6"
        assert settings.max_tokens == 4096


class TestClaudeMdDiscovery:
    def test_discover_in_project(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# Project instructions")
        discovery = ClaudeMdDiscovery(tmp_path)
        found = discovery.discover()
        assert any(p.name == "CLAUDE.md" for p in found)

    def test_discover_empty(self, tmp_path):
        discovery = ClaudeMdDiscovery(tmp_path)
        found = discovery.discover()
        # May find home dir CLAUDE.md
        for p in found:
            assert p.name == "CLAUDE.md"

    def test_load_merged(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("project rules here")
        discovery = ClaudeMdDiscovery(tmp_path)
        merged = discovery.load_merged()
        assert "project rules here" in merged


class TestMemorySystem:
    def test_save_and_list(self, tmp_path):
        mem = MemorySystem(tmp_path / "memory")
        entry = MemoryEntry(
            name="test memory",
            description="a test",
            memory_type="project",
            content="some content",
        )
        path = mem.save(entry)
        assert path.exists()

        entries = mem.list_entries()
        assert len(entries) == 1
        assert entries[0].name == "test memory"

    def test_get(self, tmp_path):
        mem = MemorySystem(tmp_path / "memory")
        entry = MemoryEntry(
            name="find me",
            description="searchable",
            memory_type="feedback",
            content="important feedback",
        )
        mem.save(entry)
        found = mem.get("find me")
        assert found is not None
        assert found.content == "important feedback"

    def test_get_missing(self, tmp_path):
        mem = MemorySystem(tmp_path / "memory")
        assert mem.get("nonexistent") is None

    def test_delete(self, tmp_path):
        mem = MemorySystem(tmp_path / "memory")
        entry = MemoryEntry(
            name="deletable",
            description="will be deleted",
            memory_type="project",
            content="temp",
        )
        mem.save(entry)
        assert mem.delete("deletable")
        assert mem.get("deletable") is None

    def test_delete_missing(self, tmp_path):
        mem = MemorySystem(tmp_path / "memory")
        assert not mem.delete("nonexistent")

    def test_index_updated(self, tmp_path):
        mem = MemorySystem(tmp_path / "memory")
        entry = MemoryEntry(
            name="indexed",
            description="in the index",
            memory_type="user",
            content="data",
        )
        mem.save(entry)
        index = (tmp_path / "memory" / "MEMORY.md").read_text()
        assert "indexed" in index

    def test_empty_dir(self, tmp_path):
        mem = MemorySystem(tmp_path / "no_such_dir")
        assert mem.list_entries() == []

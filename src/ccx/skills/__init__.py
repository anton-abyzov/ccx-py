"""Skill system: load and execute markdown-defined skills."""

from ccx.skills.discover import discover_all_skills
from ccx.skills.executor import SkillExecutor
from ccx.skills.loader import Skill, SkillLoader

__all__ = ["Skill", "SkillExecutor", "SkillLoader", "discover_all_skills"]

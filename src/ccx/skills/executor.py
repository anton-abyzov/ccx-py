"""Skill executor: inject skill content into conversation context."""

from __future__ import annotations

from ccx.skills.loader import Skill, SkillLoader


class SkillExecutor:
    """Executes skills by injecting their content into the system prompt."""

    def __init__(self, loader: SkillLoader) -> None:
        self.loader = loader
        self._active_skills: list[Skill] = []

    def activate(self, name: str) -> Skill | None:
        """Activate a skill for the current session."""
        skill = self.loader.load(name)
        if skill:
            self._active_skills.append(skill)
        return skill

    def deactivate(self, name: str) -> bool:
        """Deactivate a skill."""
        for i, skill in enumerate(self._active_skills):
            if skill.name == name:
                self._active_skills.pop(i)
                return True
        return False

    def get_system_prompt_additions(self) -> str:
        """Get skill content to append to the system prompt."""
        if not self._active_skills:
            return ""

        sections = []
        for skill in self._active_skills:
            sections.append(f"<skill name=\"{skill.name}\">\n{skill.content}\n</skill>")
        return "\n\n".join(sections)

    def match_trigger(self, user_input: str) -> list[Skill]:
        """Find skills whose trigger pattern matches the input."""
        matches = []
        for skill in self.loader.discover():
            if skill.trigger and skill.trigger.lower() in user_input.lower():
                matches.append(skill)
        return matches

    @property
    def active_skills(self) -> list[Skill]:
        return list(self._active_skills)

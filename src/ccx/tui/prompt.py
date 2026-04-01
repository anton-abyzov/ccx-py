"""Prompt toolkit session with slash command autocomplete."""

from __future__ import annotations

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from ccx.skills.discover import discover_all_skills

SLASH_COMMANDS: dict[str, str] = {
    "/help": "Show available commands",
    "/exit": "Quit the session",
    "/clear": "Clear the screen",
    "/cost": "Show token usage and cost",
    "/model": "Show current model",
    "/compact": "Compress conversation context",
    "/version": "Show version info",
    "/tools": "List available tools",
}


class SlashCompleter(Completer):
    """Autocomplete slash commands and discovered skills."""

    def __init__(self) -> None:
        self.builtin = SLASH_COMMANDS
        self.skills = discover_all_skills()

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return

        # Built-in commands first
        for cmd, desc in self.builtin.items():
            if cmd.startswith(text):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=cmd,
                    display_meta=desc,
                )

        # Then discovered skills
        for name, desc in self.skills.items():
            cmd = f"/{name}"
            if cmd.startswith(text):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=cmd,
                    display_meta=desc[:50],
                )


def create_session() -> PromptSession:
    """Create a prompt_toolkit session with autocomplete and history."""
    style = Style.from_dict({
        "prompt": "#cc7850 bold",
        "completion-menu.completion": "bg:#333333 #ffffff",
        "completion-menu.completion.current": "bg:#cc7850 #ffffff",
        "completion-menu.meta.completion": "bg:#333333 #888888",
        "completion-menu.meta.completion.current": "bg:#cc7850 #dddddd",
    })

    history_path = Path.home() / ".ccx_history"

    return PromptSession(
        message=[("class:prompt", "> ")],
        completer=SlashCompleter(),
        history=FileHistory(str(history_path)),
        style=style,
        complete_while_typing=True,
    )

"""Chat display widget for the TUI."""

from __future__ import annotations

from rich.markdown import Markdown
from rich.text import Text
from textual.widgets import RichLog


class ChatDisplay(RichLog):
    """Scrolling chat display that renders markdown and tool output."""

    DEFAULT_CSS = """
    ChatDisplay {
        height: 1fr;
        border: solid $accent;
        overflow-y: auto;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs: object) -> None:
        super().__init__(highlight=True, markup=True, wrap=True, id="chat-display", **kwargs)

    def add_user_message(self, text: str) -> None:
        """Display a user message."""
        self.write(Text(f"\n> {text}", style="bold cyan"))

    def add_assistant_text(self, text: str) -> None:
        """Display assistant text (supports streaming chunk by chunk)."""
        try:
            self.write(Markdown(text))
        except Exception:
            self.write(Text(text))

    def add_thinking(self, text: str) -> None:
        """Display thinking/reasoning text."""
        self.write(Text(f"  💭 {text}", style="dim italic"))

    def add_tool_use(self, name: str, tool_id: str) -> None:
        """Display a tool invocation."""
        self.write(Text(f"  ⚙ {name} [{tool_id[:8]}]", style="yellow"))

    def add_tool_result(self, name: str, output: str, is_error: bool) -> None:
        """Display tool execution result."""
        style = "red" if is_error else "dim"
        prefix = "✗" if is_error else "✓"
        # Truncate long output for display
        display = output[:500] + "..." if len(output) > 500 else output
        self.write(Text(f"  {prefix} {name}: {display}", style=style))

    def add_system(self, text: str) -> None:
        """Display a system message."""
        self.write(Text(f"[{text}]", style="dim green"))

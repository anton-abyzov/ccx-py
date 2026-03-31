"""Input widget for the TUI."""

from __future__ import annotations

from textual import on
from textual.message import Message
from textual.widgets import Input


class UserInput(Input):
    """Text input with submit-on-enter behavior."""

    DEFAULT_CSS = """
    UserInput {
        dock: bottom;
        height: 3;
        border: solid $primary;
        padding: 0 1;
    }
    """

    class Submitted(Message):
        """Emitted when user presses Enter."""

        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    def __init__(self, **kwargs: object) -> None:
        super().__init__(
            placeholder="Type a message... (Ctrl+C to quit)",
            id="user-input",
            **kwargs,
        )

    @on(Input.Submitted)
    def on_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key press."""
        text = event.value.strip()
        if text:
            self.post_message(UserInput.Submitted(text))
            self.value = ""

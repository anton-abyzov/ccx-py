"""Main Textual application for CCX."""

from __future__ import annotations

import asyncio
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Static

from ccx.api.client import ClaudeClient
from ccx.api.types import MessageRequest
from ccx.core.context import SessionContext
from ccx.core.query import QueryEngine
from ccx.tools.registry import ToolRegistry
from ccx.tui.chat import ChatDisplay
from ccx.tui.input import UserInput


class StatusBar(Static):
    """Bottom status bar showing model and token count."""

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    """

    def update_status(self, model: str, tokens: int) -> None:
        self.update(f" {model} | tokens: {tokens:,}")


class CcxApp(App[None]):
    """Terminal UI for CCX - AI coding assistant."""

    CSS_PATH = "styles.css"
    TITLE = "ccx-py"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear", "Clear"),
    ]

    def __init__(
        self,
        client: ClaudeClient | None = None,
        registry: ToolRegistry | None = None,
        context: SessionContext | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._api_client = client
        self._tools = registry or ToolRegistry()
        self._session = context or SessionContext()
        self._query_engine: QueryEngine | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield ChatDisplay()
        yield StatusBar()
        yield UserInput()
        yield Footer()

    def on_mount(self) -> None:
        chat = self.query_one(ChatDisplay)
        chat.add_system(f"ccx-py v0.1.0 | model: {self._session.model}")
        chat.add_system("Type a message to start. Ctrl+C to quit.")

        if self._api_client:
            self._query_engine = QueryEngine(
                client=self._api_client,
                registry=self._tools,
                context=self._context,
                on_text=lambda t: chat.add_assistant_text(t),
                on_thinking=lambda t: chat.add_thinking(t),
                on_tool_use=lambda n, tid, _: chat.add_tool_use(n, tid),
                on_tool_result=lambda n, o, e: chat.add_tool_result(n, o, e),
            )

    async def on_user_input_user_submitted(self, event: UserInput.UserSubmitted) -> None:
        """Handle user message submission."""
        text = event.value
        chat = self.query_one(ChatDisplay)
        status = self.query_one(StatusBar)

        chat.add_user_message(text)
        self._session.add_user_message(text)

        if not self._query_engine:
            chat.add_system("No API client configured. Set ANTHROPIC_API_KEY.")
            return

        try:
            await self._query_engine.run()
        except Exception as e:
            chat.add_system(f"Error: {e}")

        status.update_status(self._session.model, self._session.token_count)

    def action_clear(self) -> None:
        chat = self.query_one(ChatDisplay)
        chat.clear()

    def action_quit(self) -> None:
        self.exit()

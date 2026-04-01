"""Inline Rich-based rendering for chat mode (not Textual)."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def render_welcome(model: str, auth: str, cwd: str, tool_count: int) -> None:
    """Print a welcome banner with session info."""
    info = Text()
    info.append("Model: ", style="dim")
    info.append(model, style="bold")
    info.append("  |  Auth: ", style="dim")
    info.append(auth, style="bold")
    info.append("  |  Tools: ", style="dim")
    info.append(str(tool_count), style="bold")
    info.append("\n")
    info.append("cwd: ", style="dim")
    info.append(cwd, style="")
    info.append("\n\n", style="dim")
    info.append("Type /help for commands, Tab for autocomplete", style="dim italic")

    console.print(Panel(info, title="[bold]ccx-py[/bold]", border_style="#cc7850"))


def render_user_message(text: str) -> None:
    """Display the user's message inline."""
    console.print(f"[bold on grey23] > {text} [/]")


def render_assistant_text(text: str) -> None:
    """Display assistant response text."""
    from rich.markdown import Markdown

    console.print(Markdown(text))


def render_tool_start(name: str, detail: str) -> None:
    """Display a tool invocation indicator."""
    console.print(f"  [green]●[/] [bold]{name}[/]([dim]{detail}[/])")


def render_tool_output(name: str, output: str, is_error: bool = False) -> None:
    """Display tool execution result."""
    if is_error:
        console.print(f"[red]x {name}: {output}[/]")
    else:
        display = output[:500] + "..." if len(output) > 500 else output
        console.print(f"[dim]  {name}: {display}[/]")


def render_separator() -> None:
    """Print a visual separator between exchanges."""
    console.rule(style="dim")

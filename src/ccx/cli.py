"""CLI entry point using Click."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

from ccx import __version__


def _setup_registry() -> object:
    """Create and populate the default tool registry."""
    from ccx.tools.agent_tool import AgentTool
    from ccx.tools.bash import BashTool
    from ccx.tools.file_edit import FileEditTool
    from ccx.tools.file_read import FileReadTool
    from ccx.tools.file_write import FileWriteTool
    from ccx.tools.glob_tool import GlobTool
    from ccx.tools.grep import GrepTool
    from ccx.tools.notebook_edit import NotebookEditTool
    from ccx.tools.registry import ToolRegistry
    from ccx.tools.todo_write import TodoWriteTool
    from ccx.tools.web_fetch import WebFetchTool
    from ccx.tools.web_search import WebSearchTool

    registry = ToolRegistry()
    registry.register(BashTool())
    registry.register(FileReadTool())
    registry.register(FileWriteTool())
    registry.register(FileEditTool())
    registry.register(GlobTool())
    registry.register(GrepTool())
    registry.register(WebFetchTool())
    registry.register(AgentTool())
    registry.register(WebSearchTool())
    registry.register(TodoWriteTool())
    registry.register(NotebookEditTool())
    return registry


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="ccx-py")
@click.option("--model", "-m", default=None, help="Model to use.")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", default=None, help="API key.")
@click.option("--tui", is_flag=True, default=False, help="Launch full-screen Textual TUI.")
@click.pass_context
def main(ctx: click.Context, model: str | None, api_key: str | None, tui: bool) -> None:
    """CCX Python - AI coding assistant CLI."""
    ctx.ensure_object(dict)
    ctx.obj["model"] = model
    ctx.obj["api_key"] = api_key

    if ctx.invoked_subcommand is None:
        if tui:
            _launch_tui_sync(model, api_key)
        else:
            ctx.invoke(chat)


@main.command()
@click.argument("prompt")
@click.option("--model", "-m", default=None, help="Model override.")
@click.pass_context
def ask(ctx: click.Context, prompt: str, model: str | None) -> None:
    """Send a one-shot prompt (non-interactive)."""
    api_key = ctx.obj.get("api_key")
    model = model or ctx.obj.get("model") or "claude-sonnet-4-6"
    asyncio.run(_oneshot(prompt, model, api_key))


@main.command()
def version() -> None:
    """Show version info."""
    click.echo(f"ccx-py {__version__}")
    click.echo(f"Python {sys.version}")


@main.command()
@click.option("--model", "-m", default=None, help="Model override.")
@click.pass_context
def chat(ctx: click.Context, model: str | None) -> None:
    """Interactive chat with slash command autocomplete."""
    from ccx.skills.loader import SkillLoader
    from ccx.tui.inline_render import (
        render_separator,
        render_user_message,
        render_welcome,
    )
    from ccx.tui.prompt import SLASH_COMMANDS, create_session

    api_key = ctx.obj.get("api_key")
    model = model or ctx.obj.get("model") or "claude-sonnet-4-6"

    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set", err=True)
        sys.exit(1)

    registry = _setup_registry()
    skill_executor = SkillLoader()
    render_welcome(model, "API Key", str(Path.cwd()), len(registry.list_tools()))

    session = create_session()

    while True:
        try:
            text = session.prompt()
            text = text.strip()
            if not text:
                continue

            if text == "/exit":
                break
            if text == "/help":
                for cmd, desc in SLASH_COMMANDS.items():
                    click.echo(f"  {cmd:12s} {desc}")
                continue
            if text == "/clear":
                click.clear()
                continue
            if text == "/version":
                click.echo(f"ccx-py {__version__}")
                continue
            if text == "/tools":
                for tool in registry.list_tools():
                    click.echo(f"  {tool.name}")
                continue
            if text == "/model":
                click.echo(f"  Model: {model}")
                continue
            if text.startswith("/"):
                # Try as a skill invocation
                parts = text[1:].split(" ", 1)
                skill_name = parts[0]
                skill_args = parts[1] if len(parts) > 1 else ""
                skill = skill_executor.load(skill_name)
                if skill:
                    click.echo(f"  [skill:{skill.name}] {skill.description}")
                    skill_prompt = skill.content
                    if skill_args:
                        skill_prompt = f"{skill.content}\n\nUser args: {skill_args}"
                    render_user_message(f"/{skill.name} {skill_args}".strip())
                    asyncio.run(_chat_turn(skill_prompt, model, api_key, registry))
                    render_separator()
                else:
                    click.echo(f"Unknown command: {text}. Type /help for available commands.")
                continue

            render_user_message(text)
            # Stream response from Claude
            asyncio.run(_chat_turn(text, model, api_key, registry))
            render_separator()
        except (KeyboardInterrupt, EOFError):
            break


async def _chat_turn(
    prompt: str, model: str, api_key: str, registry: object
) -> None:
    """Run a single chat turn with streaming output."""
    from rich.console import Console
    from rich.markdown import Markdown

    from ccx.api.client import ClaudeClient
    from ccx.api.types import TextContent
    from ccx.config.claudemd import ClaudeMdDiscovery
    from ccx.core.context import SessionContext
    from ccx.core.prompt import build_system_prompt
    from ccx.core.query import QueryEngine

    console = Console()

    context = SessionContext(model=model)
    context.add_user_message(prompt)

    discovery = ClaudeMdDiscovery()
    claude_md = discovery.load_merged()
    context.system_prompt = build_system_prompt(
        tools=registry.list_tools(),
        working_dir=context.working_dir,
        claude_md=claude_md,
    )

    async with ClaudeClient(api_key=api_key, model=model) as client:
        engine = QueryEngine(
            client=client,
            registry=registry,
            context=context,
            on_text=lambda t: None,
        )
        content_blocks = await engine.run()

    for block in content_blocks:
        if isinstance(block, TextContent):
            console.print(Markdown(block.text))


def _launch_tui_sync(model: str | None, api_key: str | None) -> None:
    """Launch the Textual TUI using Textual's own event loop."""
    from ccx.api.client import ClaudeClient
    from ccx.config.claudemd import ClaudeMdDiscovery
    from ccx.config.settings import Settings
    from ccx.core.context import SessionContext
    from ccx.tui.app import CcxApp

    settings = Settings.load()
    effective_key = api_key or settings.api_key
    effective_model = model or settings.model

    if not effective_key:
        click.echo("Error: ANTHROPIC_API_KEY not set. Pass --api-key or set the env var.", err=True)
        sys.exit(1)

    context = SessionContext(
        model=effective_model,
        working_dir=Path.cwd(),
    )

    # Load CLAUDE.md instructions
    discovery = ClaudeMdDiscovery()
    instructions = discovery.load_merged()
    if instructions:
        context.system_prompt = instructions

    client = ClaudeClient(api_key=effective_key, model=effective_model)
    registry = _setup_registry()

    app = CcxApp(client=client, registry=registry, context=context)
    app.run()  # Textual manages its own event loop


async def _oneshot(prompt: str, model: str, api_key: str | None) -> None:
    """Run a single prompt and print the result."""
    from rich.console import Console
    from rich.markdown import Markdown

    from ccx.api.client import ClaudeClient
    from ccx.api.types import TextContent
    from ccx.core.context import SessionContext
    from ccx.core.query import QueryEngine

    console = Console()

    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not set[/red]")
        sys.exit(1)

    from ccx.config.claudemd import ClaudeMdDiscovery
    from ccx.core.prompt import build_system_prompt

    context = SessionContext(model=model)
    context.add_user_message(prompt)

    registry = _setup_registry()

    # Build system prompt with tools and CLAUDE.md
    discovery = ClaudeMdDiscovery()
    claude_md = discovery.load_merged()
    context.system_prompt = build_system_prompt(
        tools=registry.list_tools(),
        working_dir=context.working_dir,
        claude_md=claude_md,
    )

    async with ClaudeClient(api_key=api_key, model=model) as client:
        engine = QueryEngine(
            client=client,
            registry=registry,
            context=context,
            on_text=lambda t: None,
        )
        content_blocks = await engine.run()

    # Print text content
    for block in content_blocks:
        if isinstance(block, TextContent):
            console.print(Markdown(block.text))


if __name__ == "__main__":
    main()

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
@click.pass_context
def main(ctx: click.Context, model: str | None, api_key: str | None) -> None:
    """CCX Python - AI coding assistant CLI."""
    ctx.ensure_object(dict)
    ctx.obj["model"] = model
    ctx.obj["api_key"] = api_key

    if ctx.invoked_subcommand is None:
        # Default: launch TUI
        asyncio.run(_launch_tui(model, api_key))


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


async def _launch_tui(model: str | None, api_key: str | None) -> None:
    """Launch the Textual TUI."""
    from ccx.api.client import ClaudeClient
    from ccx.config.claudemd import ClaudeMdDiscovery
    from ccx.config.settings import Settings
    from ccx.core.context import SessionContext
    from ccx.tui.app import CcxApp

    settings = Settings.load()
    effective_key = api_key or settings.api_key
    effective_model = model or settings.model

    context = SessionContext(
        model=effective_model,
        working_dir=Path.cwd(),
    )

    # Load CLAUDE.md instructions
    discovery = ClaudeMdDiscovery()
    instructions = discovery.load_merged()
    if instructions:
        context.system_prompt = instructions

    client = ClaudeClient(api_key=effective_key, model=effective_model) if effective_key else None
    registry = _setup_registry()

    app = CcxApp(client=client, registry=registry, context=context)
    await app.run_async()

    if client:
        await client.close()


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

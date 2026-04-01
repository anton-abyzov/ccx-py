"""CLI entry point using Click."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

from ccx import __version__


def _summarize_tool_input(name: str, inp: dict) -> str:
    """Create a short display string for tool input args."""
    if name == "bash":
        return inp.get("command", "")[:80]
    if name in ("file_read", "file_write", "file_edit"):
        return inp.get("file_path", "")
    if name == "glob":
        return inp.get("pattern", "")
    if name == "grep":
        return inp.get("pattern", "")
    if name == "web_fetch":
        return inp.get("url", "")[:80]
    # Generic: show first string value
    for v in inp.values():
        if isinstance(v, str):
            return v[:60]
    return ""


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
    from ccx.tools.plan_mode import EnterPlanModeTool, ExitPlanModeTool
    from ccx.tools.registry import ToolRegistry
    from ccx.tools.send_message import SendMessageTool
    from ccx.tools.task_create import TaskCreateTool
    from ccx.tools.task_list import TaskListTool
    from ccx.tools.task_update import TaskUpdateTool
    from ccx.tools.team_create import TeamCreateTool
    from ccx.tools.team_delete import TeamDeleteTool
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
    registry.register(TeamCreateTool())
    registry.register(TeamDeleteTool())
    registry.register(SendMessageTool())
    registry.register(TaskCreateTool())
    registry.register(TaskUpdateTool())
    registry.register(TaskListTool())
    registry.register(EnterPlanModeTool())
    registry.register(ExitPlanModeTool())
    return registry


def _resolve_permission_mode(dangerously_skip_permissions: bool, permission_mode: str) -> str:
    """Resolve effective permission mode from CLI flags."""
    from ccx.permissions.modes import PermissionMode

    if dangerously_skip_permissions:
        return PermissionMode.BYPASS
    try:
        return PermissionMode(permission_mode)
    except ValueError:
        return PermissionMode.BYPASS


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="ccx-py")
@click.option("--model", "-m", default=None, help="Model to use.")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", default=None, help="API key.")
@click.option("--provider", default="anthropic", help="API provider: anthropic, openrouter.")
@click.option("--openrouter-key", envvar="OPENROUTER_API_KEY", default=None, help="OpenRouter API key.")
@click.option("--tui", is_flag=True, default=False, help="Launch full-screen Textual TUI.")
@click.option("--dangerously-skip-permissions/--no-dangerously-skip-permissions", default=True, help="Skip all permission prompts (default: true).")
@click.option("--permission-mode", default="bypass", help="Permission mode: default, acceptEdits, bypass, plan.")
@click.pass_context
def main(ctx: click.Context, model: str | None, api_key: str | None, provider: str, openrouter_key: str | None, tui: bool, dangerously_skip_permissions: bool, permission_mode: str) -> None:
    """CCX Python - AI coding assistant CLI."""
    ctx.ensure_object(dict)
    ctx.obj["model"] = model
    ctx.obj["api_key"] = api_key
    ctx.obj["provider"] = provider
    ctx.obj["openrouter_key"] = openrouter_key
    ctx.obj["permission_mode"] = _resolve_permission_mode(dangerously_skip_permissions, permission_mode)

    if ctx.invoked_subcommand is None:
        if tui:
            _launch_tui_sync(model, api_key)
        else:
            ctx.invoke(chat)


@main.command()
@click.argument("prompt")
@click.option("--model", "-m", default=None, help="Model override.")
@click.option("--provider", default=None, help="API provider override.")
@click.pass_context
def ask(ctx: click.Context, prompt: str, model: str | None, provider: str | None) -> None:
    """Send a one-shot prompt (non-interactive)."""
    api_key = ctx.obj.get("api_key")
    provider = provider or ctx.obj.get("provider", "anthropic")
    openrouter_key = ctx.obj.get("openrouter_key")
    perm_mode = ctx.obj.get("permission_mode")

    if provider == "openrouter":
        model = model or ctx.obj.get("model") or "nvidia/nemotron-3-super-120b-a12b:free"
        asyncio.run(_oneshot(prompt, model, None, permission_mode=perm_mode, provider=provider, openrouter_key=openrouter_key))
    else:
        model = model or ctx.obj.get("model") or "claude-sonnet-4-6"
        asyncio.run(_oneshot(prompt, model, api_key, permission_mode=perm_mode))


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
    from ccx.config.auth import resolve_auth
    from ccx.skills.loader import SkillLoader
    from ccx.tui.inline_render import (
        render_separator,
        render_user_message,
        render_welcome,
    )
    from ccx.tui.prompt import SLASH_COMMANDS, create_session

    perm_mode = ctx.obj.get("permission_mode")
    provider = ctx.obj.get("provider", "anthropic")
    openrouter_key = ctx.obj.get("openrouter_key")

    explicit_key = ctx.obj.get("api_key")

    if provider == "openrouter":
        model = model or ctx.obj.get("model") or "nvidia/nemotron-3-super-120b-a12b:free"
        api_key = openrouter_key or ""
        is_oauth = False
        auth_display = "OpenRouter"
    else:
        model = model or ctx.obj.get("model") or "claude-sonnet-4-6"
        if explicit_key:
            api_key, is_oauth, auth_display = explicit_key, False, "API Key"
        else:
            try:
                api_key, is_oauth, auth_display = resolve_auth()
            except RuntimeError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

    registry = _setup_registry()
    skill_executor = SkillLoader()
    render_welcome(model, auth_display, str(Path.cwd()), len(registry.list_tools()))

    session = create_session()

    while True:
        try:
            text = session.prompt()
            sys.stdout.write("\033[A\033[2K\r")
            sys.stdout.flush()
            text = text.strip()
            if not text:
                continue

            render_user_message(text)

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
            if text == "/login":
                from ccx.config.oauth import run_oauth_login
                run_oauth_login()
                continue
            if text.startswith("/"):
                parts = text[1:].split(" ", 1)
                skill_name = parts[0]
                skill_args = parts[1] if len(parts) > 1 else ""
                skill = skill_executor.load(skill_name)
                if skill:
                    skill_prompt = skill.content
                    if skill_args:
                        skill_prompt = f"{skill.content}\n\nUser args: {skill_args}"
                    asyncio.run(_chat_turn(skill_prompt, model, api_key, registry, use_oauth=is_oauth, permission_mode=perm_mode, provider=provider))
                    render_separator()
                else:
                    click.echo(f"Unknown command: {text}. Type /help for available commands.")
                continue

            asyncio.run(_chat_turn(text, model, api_key, registry, use_oauth=is_oauth, permission_mode=perm_mode, provider=provider))
            render_separator()
        except (KeyboardInterrupt, EOFError):
            break


def _make_client(provider: str, api_key: str, model: str, *, use_oauth: bool = False) -> object:
    """Create the appropriate API client based on provider."""
    if provider == "openrouter":
        from ccx.api.openai_client import OpenAIClient
        return OpenAIClient(api_key=api_key, model=model)
    from ccx.api.client import ClaudeClient
    return ClaudeClient(api_key=api_key, model=model, use_oauth=use_oauth)


async def _chat_turn(
    prompt: str, model: str, api_key: str, registry: object, *, use_oauth: bool = False, permission_mode=None, provider: str = "anthropic"
) -> None:
    """Run a single chat turn with streaming output."""
    from rich.console import Console
    from rich.markdown import Markdown

    from ccx.api.types import TextContent
    from ccx.config.claudemd import ClaudeMdDiscovery
    from ccx.core.context import SessionContext
    from ccx.core.prompt import build_system_prompt
    from ccx.core.query import QueryEngine
    from ccx.permissions.modes import PermissionMode
    from ccx.tui.inline_render import render_tool_output, render_tool_start

    console = Console()
    effective_mode = permission_mode or PermissionMode.BYPASS

    context = SessionContext(model=model)
    context.add_user_message(prompt)

    discovery = ClaudeMdDiscovery()
    claude_md = discovery.load_merged()
    context.system_prompt = build_system_prompt(
        tools=registry.list_tools(),
        working_dir=context.working_dir,
        claude_md=claude_md,
    )

    client_ctx = _make_client(provider, api_key, model, use_oauth=use_oauth)
    async with client_ctx as client:
        engine = QueryEngine(
            client=client,
            registry=registry,
            context=context,
            permission_mode=effective_mode,
            on_text=lambda t: None,
            on_tool_use=lambda name, tid, inp: render_tool_start(name, _summarize_tool_input(name, inp)),
            on_tool_result=lambda name, output, is_err: render_tool_output(name, output, is_err),
        )
        content_blocks = await engine.run()

    for block in content_blocks:
        if isinstance(block, TextContent):
            console.print(Markdown(block.text))


def _launch_tui_sync(model: str | None, api_key: str | None) -> None:
    """Launch the Textual TUI using Textual's own event loop."""
    from ccx.api.client import ClaudeClient
    from ccx.config.auth import resolve_auth
    from ccx.config.claudemd import ClaudeMdDiscovery
    from ccx.config.settings import Settings
    from ccx.core.context import SessionContext
    from ccx.tui.app import CcxApp

    settings = Settings.load()
    effective_model = model or settings.model

    # Resolve auth: explicit key → env var → keychain → credentials file
    if api_key:
        effective_key, is_oauth = api_key, False
    else:
        try:
            effective_key, is_oauth, _ = resolve_auth()
        except RuntimeError as e:
            click.echo(f"Error: {e}", err=True)
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

    client = ClaudeClient(api_key=effective_key, model=effective_model, use_oauth=is_oauth)
    registry = _setup_registry()

    app = CcxApp(client=client, registry=registry, context=context)
    app.run()  # Textual manages its own event loop


async def _oneshot(prompt: str, model: str, api_key: str | None, permission_mode=None, provider: str = "anthropic", openrouter_key: str | None = None) -> None:
    """Run a single prompt and print the result."""
    from rich.console import Console
    from rich.markdown import Markdown

    from ccx.api.types import TextContent
    from ccx.core.context import SessionContext
    from ccx.core.query import QueryEngine
    from ccx.permissions.modes import PermissionMode
    from ccx.tui.inline_render import render_tool_output, render_tool_start

    console = Console()
    effective_mode = permission_mode or PermissionMode.BYPASS

    if provider == "openrouter":
        effective_key = openrouter_key or ""
        is_oauth = False
    elif api_key:
        effective_key, is_oauth = api_key, False
    else:
        from ccx.config.auth import resolve_auth
        try:
            effective_key, is_oauth, _ = resolve_auth()
        except RuntimeError as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    from ccx.config.claudemd import ClaudeMdDiscovery
    from ccx.core.prompt import build_system_prompt

    context = SessionContext(model=model)
    context.add_user_message(prompt)

    registry = _setup_registry()

    discovery = ClaudeMdDiscovery()
    claude_md = discovery.load_merged()
    context.system_prompt = build_system_prompt(
        tools=registry.list_tools(),
        working_dir=context.working_dir,
        claude_md=claude_md,
    )

    client_ctx = _make_client(provider, effective_key, model, use_oauth=is_oauth)
    async with client_ctx as client:
        engine = QueryEngine(
            client=client,
            registry=registry,
            context=context,
            permission_mode=effective_mode,
            on_text=lambda t: None,
            on_tool_use=lambda name, tid, inp: render_tool_start(name, _summarize_tool_input(name, inp)),
            on_tool_result=lambda name, output, is_err: render_tool_output(name, output, is_err),
        )
        content_blocks = await engine.run()

    for block in content_blocks:
        if isinstance(block, TextContent):
            console.print(Markdown(block.text))


if __name__ == "__main__":
    main()

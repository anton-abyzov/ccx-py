# ccx-py

AI coding assistant CLI in Python, part of the [CCX (Community Code Extended)](https://github.com/anton-abyzov/ccx) project. Textual TUI + prompt_toolkit autocomplete. 11 tools. Built on httpx async streaming with Pydantic v2 types.

## Why CCX?

CCX (Community Code Extended) is a custom AI coding assistant built from the ground up using publicly documented API specifications and common patterns in AI-assisted development. Each implementation is its own application with independent architecture decisions and language-idiomatic designs.

Python was the natural choice for accessibility -- with async/await, match/case, and modern type hints, it delivers a clean implementation that's easy to read, extend, and contribute to. ccx-py is a full working implementation with real async tool execution, Textual TUI, and an agent system -- not just a metadata wrapper.

Unlike [instructkr/claw-code](https://github.com/instructkr/claw-code) (41.7k stars), which takes a metadata/harness approach, ccx-py is a ground-up Python implementation with real async tool execution, Textual TUI, and a comprehensive test suite.

- Architecture analysis: https://verified-skill.com/insights/claude-code
- CCX umbrella: https://github.com/anton-abyzov/ccx

## Quick Start

```bash
git clone https://github.com/anton-abyzov/ccx-py.git
cd ccx-py
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export ANTHROPIC_API_KEY="your-key-here"
ccx chat          # Interactive with autocomplete
ccx ask "Hello"   # One-shot
```

## Features

- **11 built-in tools** -- Bash, FileRead, FileEdit, FileWrite, Glob, Grep, Agent, WebFetch, NotebookEdit, TodoRead, TodoWrite
- **Slash commands with autocomplete** -- `/help`, `/compact`, `/clear`, `/model`, `/memory`, `/skills`
- **Streaming responses** -- httpx async SSE streaming with real-time tool_use handling
- **Markdown rendering** -- Rich-powered terminal markdown
- **Skill discovery** -- loads and executes markdown-based skills
- **Async agent spawning** -- asyncio.create_task with concurrent tool execution
- **Context compaction** -- MicroCompact and AutoCompact layers
- **MCP protocol** -- JSON-RPC over stdio for tool/resource discovery
- **Permission system** -- risk classification with interactive approval flows
- **Memory persistence** -- user, project, feedback, and reference memory types
- **Hook system** -- pre/post tool execution hooks

## Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/compact` | Compress conversation context |
| `/clear` | Clear conversation history |
| `/model` | Switch Claude model |
| `/memory` | View/manage memory entries |
| `/skills` | List available skills |
| `/config` | Show current configuration |

## Why Python?

- **Zero compile step** -- edit and run immediately
- **Modern async** -- async/await, IAsyncGenerator for streaming, asyncio for concurrency
- **Textual TUI** -- full terminal UI framework (not just Rich)
- **Pydantic v2** -- type-safe API models with automatic validation
- **Accessible** -- easy to read, extend, and contribute to
- **Rich ecosystem** -- httpx, Click, pytest-asyncio

## Architecture

Based on publicly documented patterns in AI coding assistant architecture:

- **Tool System**: Async tools with risk classification and concurrent execution
- **Agent Spawning**: asyncio.create_task with structured concurrency
- **TUI**: Textual framework with chat display and interactive prompts
- **Context Management**: MicroCompact + AutoCompact compression layers
- **MCP Protocol**: JSON-RPC over stdio client
- **Permission System**: Risk-based classification with interactive approval
- **Streaming API**: httpx async with SSE parsing and tool_use handling

## Tech Stack

| Component | Library |
|-----------|---------|
| TUI | Textual |
| HTTP/Streaming | httpx (async) |
| API Types | Pydantic v2 |
| CLI Parsing | Click |
| Markdown | Rich |
| Async Runtime | asyncio |
| Testing | pytest + pytest-asyncio |

## Project Structure

```
src/ccx/
  api/          # Claude API client (httpx async streaming, SSE parser)
  tools/        # Tool system (bash, file ops, glob, grep, web fetch)
  core/         # Query engine (agentic loop), agent spawning
  tui/          # Textual terminal UI
  permissions/  # Risk classification, permission modes, rules
  compact/      # Context compaction (MicroCompact, AutoCompact)
  config/       # Settings, CLAUDE.md discovery, memory system
  mcp/          # Model Context Protocol client (JSON-RPC/stdio)
  skills/       # Markdown skill loader and executor
  hooks/        # Pre/post tool execution hooks
  cli.py        # Click CLI entry point
tests/          # pytest test suite
```

## Development

```bash
git clone https://github.com/anton-abyzov/ccx-py.git
cd ccx-py
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Requirements

- Python 3.11+
- Anthropic API key

## License

MIT

# ccx-py

Python implementation of an AI coding assistant CLI, part of the [CCX project](https://github.com/anton-abyzov/ccx).

## Background

On March 31, 2026, security researcher Chaofan Shou published a tweet revealing that Anthropic's Claude Code CLI tool contained its entire system prompt in plaintext within the npm package. The leaked ~100KB prompt exposed the complete architecture: tool definitions, permission models, agent spawning, context compaction, MCP integration, and more.

CCX (Claude Code eXtended) is a collection of clean-room implementations across multiple languages, built from the architectural insights in the leaked prompt. This repository is the Python implementation.

## How is this different from claw-code (instructkr/claude-code)?

The existing Python project `instructkr/claw-code` (41.7k stars) takes a metadata-driven approach: it catalogs tool and command inventories as structured data without actual execution.

| Aspect | ccx-py | claw-code |
|--------|--------|-----------|
| Approach | Working implementation | Metadata catalog |
| TUI | Textual (full terminal UI) | None |
| Tool execution | Real async subprocess | None |
| Agent system | asyncio.create_task | Task definitions |
| API client | httpx async streaming | Documentation only |
| Testing | pytest + pytest-asyncio | Verification scripts |

## Architecture

```
ccx-py/
├── src/ccx/
│   ├── api/          # Claude API client (httpx async streaming, SSE parser)
│   ├── tools/        # Tool system (bash, file ops, glob, grep, web fetch)
│   ├── core/         # Query engine (agentic loop), agent spawning
│   ├── tui/          # Textual terminal UI
│   ├── permissions/  # Risk classification, permission modes, rules
│   ├── compact/      # Context compaction (MicroCompact, AutoCompact)
│   ├── config/       # Settings, CLAUDE.md discovery, memory system
│   ├── mcp/          # Model Context Protocol client (JSON-RPC/stdio)
│   ├── skills/       # Markdown skill loader and executor
│   ├── hooks/        # Pre/post tool execution hooks
│   └── cli.py        # Click CLI entry point
└── tests/            # pytest test suite
```

## Tech Stack

- **Python 3.11+** with modern features (match/case, type hints, async for/with)
- **httpx** for async HTTP with streaming SSE
- **Pydantic v2** for all API types and validation
- **Textual** for the terminal UI (not just Rich)
- **Click** for CLI argument parsing
- **asyncio** for concurrent tool execution and agent spawning
- **pytest + pytest-asyncio** for the test suite

## Getting Started

### Prerequisites

- Python 3.11 or later
- An Anthropic API key

### Installation

```bash
git clone https://github.com/anton-abyzov/ccx-py.git
cd ccx-py
pip install -e ".[dev]"
```

### Usage

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key"

# Launch the TUI
ccx

# One-shot query
ccx ask "explain this code"

# With model override
ccx --model claude-opus-4-6 ask "refactor this function"
```

### Running Tests

```bash
pytest tests/ -v
```

## Project Status

Phase 1 (Foundation) is complete:
- API client with async streaming
- Full tool system (bash, file I/O, glob, grep, web fetch)
- Agentic query loop with parallel tool execution
- Textual TUI with chat display
- Permission system with risk classification
- Context compaction (MicroCompact + AutoCompact)
- MCP client (JSON-RPC over stdio)
- Skill system (markdown-based)
- Hook system (pre/post tool)
- Configuration (settings.json, CLAUDE.md discovery, memory)

## License

MIT

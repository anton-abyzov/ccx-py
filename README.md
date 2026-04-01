# ccx-py

Python implementation of an AI coding assistant CLI, part of the [CCX project](https://github.com/anton-abyzov/ccx).

## Background

CCX (Claude Code eXtended) is a family of clean-room AI coding assistant implementations, built as open-source alternatives to proprietary tools. Each implementation is designed from the ground up using publicly documented API specifications and common patterns in AI-assisted development. This repository is the Python implementation.

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

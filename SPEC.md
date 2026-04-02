# ccx-py Specification

## Overview

ccx-py is the Python implementation of CCX (Community Code Extended), providing a working terminal-based AI coding assistant CLI with tool execution, agent spawning, and context management.

## Phase 1: Foundation (Current)

### API Client
- Async HTTP client using httpx
- Server-Sent Events (SSE) parser for streaming responses
- Pydantic v2 models for all API types (messages, tools, content blocks)
- Support for text, thinking, and tool_use content blocks
- Token usage tracking

### Tool System
- Abstract base class with name, description, input_schema, execute
- Tool registry with register, get, list, and dispatch
- Built-in tools:
  - **bash**: async subprocess execution with timeout
  - **file_read**: line-numbered file reading with offset/limit
  - **file_write**: file creation with parent directory creation
  - **file_edit**: exact string replacement (single or replace_all)
  - **glob**: fast file pattern matching
  - **grep**: regex search (ripgrep with fallback)
  - **web_fetch**: HTTP GET with content extraction

### Query Engine
- Async agentic loop: stream response -> collect tool uses -> execute in parallel -> repeat
- Configurable callbacks for text, thinking, tool use, and tool results
- Maximum 50 tool loops as safety limit
- Parallel tool execution via asyncio.gather

### Agent System
- AgentDef for configuring sub-agents
- AgentManager for spawning and tracking asyncio tasks
- Foreground (await) and background (fire-and-forget) spawning
- Status tracking and cancellation support

### TUI
- Textual App with Header, ChatDisplay, StatusBar, UserInput, Footer
- Rich markdown rendering for assistant responses
- Tool use and result display with status indicators
- Keyboard shortcuts (Ctrl+C quit, Ctrl+L clear)

### Permissions
- Risk classification: SAFE, LOW, MEDIUM, HIGH
- Permission modes: DEFAULT, ACCEPT_EDITS, BYPASS, PLAN
- Rule-based system with glob patterns for tool names and paths
- Dangerous command detection for bash (rm -rf, sudo, force-push, etc.)

### Context Compaction
- Token estimation (~4 chars/token heuristic)
- MicroCompact: truncate tool results, then drop middle messages
- AutoCompact: threshold-based automatic compaction (80% trigger, 50% target)

### Configuration
- Settings from ~/.claude/settings.json with environment variable overrides
- CLAUDE.md discovery: walk up from project dir to home
- Memory system: YAML-frontmatter markdown files with index

### MCP
- JSON-RPC 2.0 over stdio
- Pydantic models for request/response/error
- Tool listing and invocation
- Subprocess lifecycle management

### Skills
- Markdown files with YAML frontmatter (name, description, trigger)
- Skill loader with directory discovery
- Skill executor with activation/deactivation and trigger matching

### Hooks
- Pre/post tool execution hooks
- Shell command execution with environment variables
- Exit code 2 = block the tool call
- 10-second timeout per hook

## Phase 2: Enhanced Tools

- File diff tool (unified diff output)
- Directory tree tool
- Git integration tool (status, diff, log, commit)
- Process manager tool (background processes)

## Phase 3: Advanced Features

- Multi-turn conversation persistence (SQLite)
- Session management (save/restore)
- Conversation branching
- Cost tracking and budgets

## Phase 4: IDE Integration

- VS Code extension via stdio
- JetBrains plugin support
- Language Server Protocol bridge

## Phase 5: Multi-Agent

- Agent-to-agent communication
- Team-based orchestration
- Worktree isolation for parallel agents
- Shared context and message passing

## Phase 6: Enterprise

- Custom model provider backends
- Audit logging
- Policy engine for organization-wide rules
- SSO integration

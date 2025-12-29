# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GEMMIS is a Python CLI for local LLM chat via Ollama with a Rich terminal UI, visual themes, AI personas, and tool calling capabilities.

## Commands

```bash
# Install
pip install -e ".[dev]"

# Run
gemmis                      # Start chat with defaults
gemmis -t synthwave         # Specific theme
gemmis -m qwen2.5:7b        # Specific model
gemmis setup                # Configuration wizard

# Test
pytest tests/ -v
pytest tests/test_foo.py::test_name -v  # Single test

# Lint
ruff check gemmis/ && ruff format gemmis/
```

## Architecture

```
gemmis/
├── cli.py          # Typer CLI entry point, defines commands (chat, setup, config, models)
├── app.py          # Main async event loop, Rich Live TUI, handles streaming + tool calls
├── state.py        # AppState dataclass: messages, tokens, system stats, memory refs
├── ollama_client.py # Async httpx client for Ollama API, streaming chat, tool execution
├── config.py       # Config loading from ~/.config/gemmis-cli/config.toml
├── commands.py     # In-chat slash commands (/help, /save, /theme, etc.)
├── personas.py     # AI persona system prompts
├── tools.py        # Tool definitions and executor for function calling
├── brain.py        # Optional RAG with ChromaDB (requires [rag] extra)
├── memory/
│   ├── store.py    # SQLite session persistence via aiosqlite
│   ├── session.py  # SessionManager for conversation history
│   └── vectors.py  # Optional vector store (requires chromadb)
└── ui/
    ├── theme.py    # Theme dataclass + 5 themes (nord, cyberpunk, synthwave, dracula, obsidian)
    ├── chat.py     # Chat message rendering with syntax highlighting
    ├── panels.py   # Header and stats panel rendering
    ├── boot.py     # Animated boot sequence
    └── input.py    # prompt_toolkit input session
```

## Key Patterns

- **Themes**: Always use `get_current_theme()` from `ui.theme`, never hardcode colors
- **Async**: All I/O operations use async/await; main loop in `app.py` runs with `asyncio.run()`
- **Optional deps**: ChromaDB, tiktoken are optional; code uses try/except imports with graceful fallback
- **Tool calling**: Ollama's function calling format; tools defined in `tools.py`, executed via `safe_tool_executor` for sensitive operations
- **State management**: `AppState` dataclass holds all runtime state; passed through main loop

## Code Style

- Python 3.10+ with type hints
- Imports: stdlib, third-party, local (relative `.module`)
- 4-space indent, 100 char lines (ruff format)
- Brief docstrings for modules and public functions

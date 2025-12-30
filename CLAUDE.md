# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GEMMIS is a Python CLI for local LLM chat via Ollama with a Textual TUI, visual themes, AI personas, and tool calling capabilities.

## Commands

```bash
# Install
pip install -e ".[dev]"

# Run
gemmis                      # Start chat with defaults
gemmis -t synthwave         # Specific theme
gemmis -m qwen2.5:7b        # Specific model
gemmis -p hacker            # Specific persona
gemmis --minimal            # Skip boot animation
gemmis setup                # Configuration wizard
gemmis models               # List available Ollama models

# Test
pytest tests/ -v
pytest tests/test_foo.py::test_name -v  # Single test

# Lint
ruff check gemmis/ && ruff format gemmis/
```

## Architecture

```
gemmis/
├── cli.py           # Typer CLI entry point
├── app.py           # Textual App: GemmisApp with tabbed interface (Chat/Dashboard/Docker)
├── state.py         # AppState dataclass: messages, session refs, system prompt
├── ollama_client.py # Async httpx client: streaming chat, tool execution
├── config.py        # Config from ~/.config/gemmis-cli/config.toml
├── commands.py      # In-chat slash commands (/help, /save, /theme, etc.)
├── personas.py      # AI persona system prompts (architect, hacker, assistant)
├── tools.py         # Tool definitions for function calling
├── audio.py         # Sound effects system (startup, token, success, error)
├── system_monitor.py # CPU/RAM/GPU stats via psutil
├── memory/
│   ├── store.py     # SQLite persistence via aiosqlite
│   └── session.py   # SessionManager for conversation history
└── ui/
    ├── theme.py     # Theme dataclass + themes (nord, cyberpunk, synthwave, dracula, obsidian)
    ├── css.py       # Dynamic CSS generation from current theme
    ├── boot.py      # Rich console boot animation
    ├── effects.py   # GlitchOverlay effect widget
    └── widgets/
        ├── chat.py      # Chat, ChatBubble (typewriter effect), CodeBlock
        ├── dashboard.py # SystemGauge (sparklines), ProcessCard, KillProcessModal
        ├── sidebar.py   # Model selector, session info, controls
        ├── avatar.py    # Animated avatar states (idle, thinking, speaking, error)
        ├── matrix.py    # MatrixRain background effect
        ├── particles.py # ParticleSystem for visual feedback
        └── docker.py    # Docker container management
```

## Key Patterns

- **Textual TUI**: Main app in `app.py` uses Textual's reactive system; widgets in `ui/widgets/`
- **Themes**: Use `get_current_theme()` from `ui.theme`; CSS generated dynamically in `ui.css.get_css()`
- **Widget Messages**: Custom messages (e.g., `ModelLoaded`, `ProcessKilled`, `ProcessSelect`) bubble up via `post_message()`
- **Reactive Properties**: Widgets use `reactive()` for auto-updating UI (see `ChatBubble.rendered_content`, `SystemGauge.value`)
- **Workers**: Long-running tasks use `run_worker()` or `set_interval()` for background updates
- **Async**: All I/O uses async/await; Textual handles the event loop
- **Optional deps**: ChromaDB, tiktoken are optional with try/except fallback
- **Tool calling**: Ollama function calling format; tools in `tools.py`

## Widget Conventions

- Widgets inherit from `Static` or appropriate Textual base
- Use `compose()` to yield child widgets
- Handle button presses with `on_button_pressed()` or `@on(Message)` decorator
- Custom messages extend `textual.message.Message`
- Modal screens extend `ModalScreen[ReturnType]`

## Code Style

- Python 3.10+ with type hints
- Imports: stdlib, third-party, local (relative `.module`)
- 4-space indent, 100 char lines (ruff format)

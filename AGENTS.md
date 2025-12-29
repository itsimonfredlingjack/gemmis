# Agent Guidelines

Python CLI app (Rich terminal UI) for local LLM chat via Ollama with Typer CLI.

## Build/Test Commands

```bash
pip install -e ".[dev]"       # Install with dev dependencies
gemmis --help                 # Show CLI help
gemmis -t synthwave           # Run with synthwave theme
gemmis setup                  # Run setup wizard
pytest tests/ -v              # Run all tests
pytest tests/test_foo.py::test_name  # Run single test
ruff check gemmis/ && ruff format gemmis/  # Lint and format
```

## Code Style

- **Python 3.10+** with type hints on all functions
- **Imports**: stdlib first, third-party second, local last (relative `.module`)
- **Naming**: `snake_case` functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- **Formatting**: 4-space indent, 100 char lines (ruff format)
- **Async**: Use `async/await` for I/O operations
- **Themes**: Use `get_current_theme()` from `ui.theme`, never hardcode colors
- **Errors**: Try/except with specific exceptions; graceful fallbacks for optional deps
- **Docstrings**: Brief triple-quote docstrings for modules and public functions

# GEMMIS CLI

## Project Overview

GEMMIS is a professional, visually stunning, and highly customizable command-line interface (CLI) for interacting with local Large Language Models (LLMs) through Ollama. It transforms the standard terminal chat into a dynamic neural interface with features like visual themes, AI personas, real-time system monitoring, and extensive tool-calling capabilities.

**Key Features:**
*   **Rich TUI:** Built with `Textual` and `Rich` for a modern terminal experience.
*   **Ollama Integration:** Seamlessly connects to local Ollama instances.
*   **Visual Themes:** 5 distinct themes (Nord, Cyberpunk, Synthwave, Dracula, Obsidian).
*   **AI Personas:** Configurable personalities (Architect, Hacker, Assistant, etc.).
*   **Tool Calling:** The AI can execute system commands, manage files, monitor hardware, and run Python code.
*   **System Monitoring:** Real-time stats for CPU, RAM, and GPU.

## Architecture

The project is structured as a Python package:

*   **`gemmis/`**: Core package directory.
    *   **`cli.py`**: Main entry point using `Typer`.
    *   **`app.py`**: Main application logic.
    *   **`config.py`**: Configuration management (TOML).
    *   **`tools.py`**: Implementation of AI-accessible tools (file I/O, system commands, Docker, etc.) and security logic.
    *   **`system_monitor.py`**: Hardware monitoring using `psutil`.
    *   **`ui/`**: User Interface components (TUI).
        *   **`theme.py`**: Theme definitions.
        *   **`widgets/`**: Reusable TUI widgets.
*   **`tests/`**: Test suite.
*   **`pyproject.toml`**: Project metadata and dependency configuration.

## Building and Running

### Prerequisites
*   Python 3.10+
*   Ollama running locally (`http://localhost:11434` by default)

### Installation

**For Users:**
```bash
pip install -e .
```

**For Developers:**
```bash
pip install -e ".[dev,all]"
```

### Running the Application

**Standard Start:**
```bash
gemmis
```

**With Options:**
```bash
gemmis --theme synthwave --persona hacker --model qwen2.5:7b
```

**Setup Wizard:**
```bash
gemmis setup
```

## Development Conventions

### Coding Style
*   **Linter/Formatter:** `ruff` is used for linting and formatting.
    ```bash
    ruff check gemmis/
    ruff format gemmis/
    ```
*   **Type Hinting:** Extensive use of Python type hints is encouraged.

### Testing
Tests are written using `pytest`.
```bash
pytest tests/ -v
```

### Configuration
Configuration is stored in `~/.config/gemmis-cli/config.toml`. The `gemmis/config.py` file handles loading and defaults.

### Tool Security
The `gemmis/tools.py` module defines allowed and blocked commands to ensure safety. Sensitive actions (like `write_file` or dangerous system commands) require specific handling logic in `is_sensitive()`.

## Key Commands

| Command | Description |
| :--- | :--- |
| `chat` | Start the interactive chat session. |
| `setup` | Run the configuration wizard. |
| `config` | View or edit the configuration. |
| `models` | List available Ollama models. |

## In-Chat Commands

| Command | Description |
| :--- | :--- |
| `/help` | Show available commands. |
| `/clear` | Clear the chat history. |
| `/theme <name>` | Switch visual theme. |
| `/persona <name>` | Switch AI persona. |
| `/system` | Show hardware diagnostics. |
| `/quit` | Exit the application. |

# GEMMIS CLI

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-36%20passed-brightgreen.svg)](tests/)

> Neural Interface Terminal for local LLM chat via Ollama

GEMMIS is a professional, visually stunning, and highly customizable command-line interface (CLI) for interacting with local Large Language Models (LLMs) through Ollama. It's designed for developers, researchers, and AI enthusiasts who want a powerful and aesthetically pleasing chat experience in their terminal.

With features like multiple visual themes, distinct AI personas, real-time system monitoring, and tool-calling capabilities, GEMMIS elevates the standard CLI chat into a dynamic and interactive neural interface.

## Features

- **5 Visual Themes**: Nord, Cyberpunk, Synthwave (with gradients!), Dracula, Obsidian
- **AI Personas**: Architect, Hacker, Assistant - each with unique personality
- **Syntax Highlighting**: Code blocks rendered with proper highlighting
- **Real-time Monitoring**: CPU, RAM, GPU stats with sparkline graphs
- **Tool Calling**: AI can execute system commands, read/write files
- **Interactive Setup**: First-run wizard for configuration
- **Session Management**: Save, load, and export conversations

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) running locally
- A compatible model (default: `gemma3:4b`)

## Installation

To install GEMMIS, clone the repository and install it using pip:

```bash
git clone https://github.com/gemmis/gemmis-cli.git
cd gemmis-cli
pip install -e .
```

For development, you can install with dev dependencies:

```bash
pip install -e ".[dev]"
```

## Usage Examples

Here are a few examples of how to use GEMMIS:

**1. Start a chat with the default settings:**

```bash
gemmis
```

**2. Start a chat with the "synthwave" theme and the "hacker" persona:**

```bash
gemmis -t synthwave -p hacker
```

**3. Use a specific model and skip the boot animation:**

```bash
gemmis -m qwen2.5:7b --minimal
```

**4. Run the setup wizard to configure GEMMIS:**

```bash
gemmis setup
```

**5. List the available Ollama models:**

```bash
gemmis models
```

## CLI Options

```
GEMMIS - Neural Interface Terminal for local LLM chat via Ollama

Usage: gemmis [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --model               -m      TEXT  Ollama model                             │
│ --theme               -t      TEXT  Visual theme [default: synthwave]        │
│ --persona             -p      TEXT  AI persona [default: default]            │
│ --minimal                           Skip boot animation                      │
│ --debug               -d            Enable debug                             │
│ --no-screen                         Disable alternate screen buffer          │
│ --install-completion                Install completion for the current       │
│                                     shell.                                   │
│ --show-completion                   Show completion for the current shell,   │
│                                     to copy it or customize the              │
│                                     installation.                            │
│ --help                              Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ chat     Start interactive chat session.                                     │
│ setup    Run interactive setup wizard.                                       │
│ config   Show or edit configuration.                                         │
│ models   List available Ollama models.                                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## In-Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show command list |
| `/clear` | Clear chat buffer |
| `/save [name]` | Save session |
| `/load <name>` | Load session |
| `/export [md\|txt]` | Export to file |
| `/browse [path]` | Browse directory |
| `/tokens` | Show context usage |
| `/theme [name]` | Change theme |
| `/persona [name]` | Change persona |
| `/system` | Hardware diagnostics |
| `/health` | System health check |
| `/quit` | Exit |

## Themes

| Theme | Description |
|-------|-------------|
| **Nord** | Arctic professional - frostbitten blue and snow white (default) |
| **Cyberpunk** | High-voltage neon magenta and glowing yellow |
| **Synthwave** | Retro future with purple-to-cyan gradients |
| **Dracula** | Industry standard dark theme |
| **Obsidian** | Minimalist void - deep black with gold accents |

## Personas

| Persona | Style |
|---------|-------|
| **Default** | Helpful, smart, slightly cocky |
| **Architect** | Senior software architect - design patterns and best practices |
| **Hacker** | Elite developer - terse, efficient, terminal-native |
| **Assistant** | Friendly and patient - pedagogical, beginner-friendly |

## Configuration

Config file: `~/.config/gemmis-cli/config.toml`

```toml
[ollama]
base_url = "http://localhost:11434"

[model]
name = "gemma3:4b"
temperature = 0.3

[ui]
theme = "nord"
```

## Development

```bash
# Run tests
pytest tests/ -v

# Lint and format
ruff check gemmis/ && ruff format gemmis/

# Install with all dependencies
pip install -e ".[all]"
```

## License

MIT License - see [LICENSE](LICENSE) for details.

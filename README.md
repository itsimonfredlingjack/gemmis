# GEMMIS CLI

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-36%20passed-brightgreen.svg)](tests/)

> Neural Interface Terminal for local LLM chat via Ollama

A professional CLI with stunning visual themes, real-time system monitoring, and AI personas.

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

```bash
# Install with pip
pip install -e .

# Or with dev dependencies for testing
pip install -e ".[dev]"
```

## Quick Start

```bash
# Start with defaults (Nord theme)
gemmis

# Use Synthwave theme
gemmis -t synthwave

# Use Hacker persona with specific model
gemmis -p hacker -m qwen2.5:7b

# Skip boot animation
gemmis --minimal

# Run setup wizard
gemmis setup

# List available models
gemmis models
```

## CLI Options

```
gemmis [OPTIONS] COMMAND

Options:
  --help                Show help message

Commands:
  chat      Start interactive chat (default)
  setup     Run configuration wizard
  config    Show/edit configuration
  models    List available Ollama models

Chat Options:
  -m, --model TEXT     Ollama model to use
  -t, --theme TEXT     Visual theme (nord, cyberpunk, synthwave, dracula, obsidian)
  -p, --persona TEXT   AI persona (default, architect, hacker, assistant)
  --minimal            Skip boot animation
  -V, --version        Show version
  --themes             List available themes
  --personas           List available personas
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

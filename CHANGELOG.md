# Changelog

All notable changes to GEMMIS CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Professional CLI with Typer (--version, --model, --theme, --persona, --minimal)
- 5 visual themes: Cyberpunk, Nord, Synthwave, Dracula, Obsidian
- Interactive setup wizard for first-time users
- New commands: /browse, /shell, /analyze, /tokens, /theme, /persona
- Syntax highlighting for code blocks
- Animated diagnostic boot sequence
- 3 AI personas: Architect, Hacker, Assistant
- Structured logging system
- Test suite with pytest

### Changed
- Improved error handling with specific exceptions
- Refactored app.py into smaller modules
- Updated all documentation to English
- Nord theme is now the default

### Fixed
- Avatar colors now respect current theme
- Boot animation speed optimized

## [2.0.0] - 2024-12-20

### Added
- Initial release with Rich terminal UI
- Ollama integration for local LLM chat
- Real-time streaming responses
- System monitoring panels (CPU, RAM, GPU)
- Tool calling capabilities
- Cyberpunk and Aurora themes
- Boot animation sequence
- Session save/load functionality

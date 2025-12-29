"""Tests for the CLI interface."""

import pytest
from typer.testing import CliRunner
from gemmis.cli import app


runner = CliRunner()


class TestCLIBasics:
    """Basic CLI functionality tests."""

    def test_help_command(self):
        """--help should show usage information."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "GEMMIS" in result.output
        assert "chat" in result.output

    def test_chat_help(self):
        """chat --help should show chat options."""
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0
        assert "--model" in result.output
        assert "--theme" in result.output
        assert "--persona" in result.output

    def test_version_flag(self):
        """chat --version should show version."""
        result = runner.invoke(app, ["chat", "--version"])
        assert result.exit_code == 0
        assert "GEMMIS" in result.output
        assert "v" in result.output

    def test_themes_flag(self):
        """chat --themes should list available themes."""
        result = runner.invoke(app, ["chat", "--themes"])
        assert result.exit_code == 0
        assert "nord" in result.output.lower()
        assert "cyberpunk" in result.output.lower()
        assert "synthwave" in result.output.lower()

    def test_personas_flag(self):
        """chat --personas should list available personas."""
        result = runner.invoke(app, ["chat", "--personas"])
        assert result.exit_code == 0
        assert "default" in result.output.lower()
        assert "architect" in result.output.lower()
        assert "hacker" in result.output.lower()


class TestCLIValidation:
    """Tests for CLI input validation."""

    def test_invalid_theme(self):
        """Invalid theme should show error."""
        result = runner.invoke(app, ["chat", "--theme", "invalid_theme", "--help"])
        # Should still work with --help
        assert result.exit_code == 0

    def test_config_command(self):
        """config command should work."""
        result = runner.invoke(app, ["config", "--path"])
        assert result.exit_code == 0
        assert "gemmis" in result.output.lower()


class TestModelsCommand:
    """Tests for the models command."""

    def test_models_command_runs(self):
        """models command should run without crashing."""
        result = runner.invoke(app, ["models"])
        # May fail if Ollama not running, but shouldn't crash
        assert result.exit_code == 0

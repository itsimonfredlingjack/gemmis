"""Tests for the theme system."""

import pytest
from gemmis.ui.theme import (
    Theme,
    THEMES,
    NORD,
    CYBERPUNK,
    SYNTHWAVE,
    DRACULA,
    OBSIDIAN,
    set_theme,
    get_theme,
    get_current_theme,
    list_themes,
)


class TestThemeClass:
    """Tests for the Theme dataclass."""

    def test_theme_has_required_attributes(self):
        """Theme should have all required color attributes."""
        theme = NORD
        assert hasattr(theme, "name")
        assert hasattr(theme, "primary")
        assert hasattr(theme, "secondary")
        assert hasattr(theme, "accent")
        assert hasattr(theme, "warning")
        assert hasattr(theme, "error")
        assert hasattr(theme, "success")
        assert hasattr(theme, "bg_dark")
        assert hasattr(theme, "bg_light")

    def test_theme_uppercase_aliases(self):
        """Theme should have uppercase property aliases for backwards compatibility."""
        theme = NORD
        assert theme.PRIMARY == theme.primary
        assert theme.SECONDARY == theme.secondary
        assert theme.BG_DARK == theme.bg_dark

    def test_gradient_text_without_gradient(self):
        """Themes without gradient should return styled Text."""
        text = NORD.gradient_text("Hello")
        assert text is not None
        assert len(text) == 5

    def test_gradient_text_with_gradient(self):
        """Synthwave theme should create gradient text."""
        text = SYNTHWAVE.gradient_text("Hello World")
        assert text is not None
        assert len(text) == 11


class TestThemeRegistry:
    """Tests for theme management functions."""

    def test_all_themes_registered(self):
        """All expected themes should be in THEMES dict."""
        expected = {"nord", "cyberpunk", "synthwave", "dracula", "obsidian", "aurora"}
        assert set(THEMES.keys()) == expected

    def test_list_themes(self):
        """list_themes should return all theme names."""
        themes = list_themes()
        assert "nord" in themes
        assert "cyberpunk" in themes
        assert "synthwave" in themes

    def test_get_theme_valid(self):
        """get_theme should return theme for valid name."""
        theme = get_theme("cyberpunk")
        assert theme.name == "Cyberpunk"

    def test_get_theme_invalid(self):
        """get_theme should raise ValueError for invalid name."""
        with pytest.raises(ValueError):
            get_theme("nonexistent")

    def test_set_theme_valid(self):
        """set_theme should change current theme."""
        original = get_current_theme()
        try:
            set_theme("dracula")
            current = get_current_theme()
            assert current.name == "Dracula"
        finally:
            # Restore original
            set_theme(original.name.lower())

    def test_set_theme_invalid(self):
        """set_theme should raise ValueError for invalid name."""
        with pytest.raises(ValueError):
            set_theme("nonexistent")


class TestThemeColors:
    """Tests for theme color values."""

    def test_nord_colors(self):
        """Nord theme should have correct signature colors."""
        assert "#88c0d0" in NORD.primary  # Frost blue

    def test_cyberpunk_colors(self):
        """Cyberpunk theme should have neon colors."""
        assert "#ff00ff" in CYBERPUNK.primary  # Neon magenta

    def test_synthwave_has_gradients(self):
        """Synthwave theme should have gradient colors defined."""
        assert SYNTHWAVE.gradient_start is not None
        assert SYNTHWAVE.gradient_end is not None

    def test_obsidian_minimal(self):
        """Obsidian theme should have gold accent."""
        assert "#d4af37" in OBSIDIAN.primary  # Gold

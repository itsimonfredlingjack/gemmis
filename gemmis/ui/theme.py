"""
GEMMIS UI Themes - Color palettes and styling

Five premium themes with distinct visual signatures:
- Nord: Arctic professional (default)
- Cyberpunk: High-voltage neon
- Synthwave: Retro-future gradients
- Dracula: Industry standard dark
- Obsidian: Minimalist void
"""

from dataclasses import dataclass

from rich.text import Text


@dataclass
class Theme:
    """Theme definition with all color attributes."""

    name: str
    description: str

    # Core accent colors
    primary: str
    secondary: str
    accent: str

    # Semantic colors
    warning: str
    error: str
    success: str
    dim: str

    # Backgrounds
    bg_dark: str
    bg_light: str

    # Text
    text_primary: str
    text_secondary: str

    # Borders
    border_primary: str
    border_secondary: str

    # Syntax Highlighting (Pygments style name)
    code_theme: str = "monokai"

    # Optional gradient support (for Synthwave)
    gradient_start: str | None = None
    gradient_end: str | None = None

    # Uppercase aliases for backwards compatibility
    @property
    def PRIMARY(self) -> str:
        return self.primary

    @property
    def SECONDARY(self) -> str:
        return self.secondary

    @property
    def ACCENT(self) -> str:
        return self.accent

    @property
    def WARNING(self) -> str:
        return self.warning

    @property
    def ERROR(self) -> str:
        return self.error

    @property
    def SUCCESS(self) -> str:
        return self.success

    @property
    def DIM(self) -> str:
        return self.dim

    @property
    def BG_DARK(self) -> str:
        return self.bg_dark

    @property
    def BG_LIGHT(self) -> str:
        return self.bg_light

    @property
    def TEXT_PRIMARY(self) -> str:
        return self.text_primary

    @property
    def TEXT_SECONDARY(self) -> str:
        return self.text_secondary

    @property
    def BORDER_PRIMARY(self) -> str:
        return self.border_primary

    @property
    def BORDER_SECONDARY(self) -> str:
        return self.border_secondary

    def gradient_text(self, text: str) -> Text:
        """Create gradient-colored text using 24-bit TrueColor.

        Interpolates between gradient_start and gradient_end colors
        across the text characters. Falls back to primary color if
        no gradient is defined.
        """
        if not self.gradient_start or not self.gradient_end:
            return Text(text, style=self.primary)

        result = Text()

        # Parse hex colors
        start = self._hex_to_rgb(self.gradient_start)
        end = self._hex_to_rgb(self.gradient_end)

        length = len(text)
        if length <= 1:
            return Text(text, style=f"bold #{self.gradient_start.lstrip('#')}")

        for i, char in enumerate(text):
            # Calculate interpolation factor
            t = i / (length - 1)

            # Interpolate RGB values
            r = int(start[0] + (end[0] - start[0]) * t)
            g = int(start[1] + (end[1] - start[1]) * t)
            b = int(start[2] + (end[2] - start[2]) * t)

            # Create hex color
            color = f"#{r:02x}{g:02x}{b:02x}"
            result.append(char, style=f"bold {color}")

        return result

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


# =============================================================================
# THEME DEFINITIONS
# =============================================================================

# Nord - Arctic Professional (Default)
# Frostbitten blue and snow white. Clean, modern development environment.
NORD = Theme(
    name="Nord",
    description="Arctic Professional - Frostbitten blue and snow white",
    primary="bold #88c0d0",  # Frost blue
    secondary="bold #81a1c1",  # Lighter frost
    accent="bold #eceff4",  # Snow white
    warning="bold #ebcb8b",  # Aurora yellow
    error="bold #bf616a",  # Aurora red
    success="bold #a3be8c",  # Aurora green
    dim="#4c566a",  # Polar night
    bg_dark="#2e3440",  # Polar night
    bg_light="#3b4252",  # Polar night lighter
    text_primary="#eceff4",  # Snow storm
    text_secondary="#d8dee9",  # Snow storm
    border_primary="#88c0d0",  # Frost
    border_secondary="#5e81ac",  # Frost darker
    code_theme="nord",
)

# Cyberpunk - High-Voltage Neon
# Neon magenta and glowing yellow. Intense, edgy, futuristic.
CYBERPUNK = Theme(
    name="Cyberpunk",
    description="High-Voltage - Neon magenta and glowing yellow",
    primary="bold #ff00ff",  # Neon Magenta
    secondary="bold #00ffff",  # Cyan
    accent="bold #ffff00",  # Glowing Yellow
    warning="bold #ffff00",  # Yellow
    error="bold #ff0044",  # Hot Red
    success="bold #00ff00",  # Neon Green
    dim="#666666",  # Dark grey
    bg_dark="#0a0a0a",  # Near black
    bg_light="#1a1a2e",  # Dark purple
    text_primary="#ffffff",  # White
    text_secondary="#ff99ff",  # Light magenta
    border_primary="#ff00ff",  # Magenta
    border_secondary="#00ffff",  # Cyan
    code_theme="fruity",
)

# Synthwave '84 - Retro Future
# Purple to cyan gradients. 24-bit TrueColor gradient effects.
SYNTHWAVE = Theme(
    name="Synthwave",
    description="Retro Future - Purple to cyan gradients",
    primary="bold #f97ff5",  # Hot pink
    secondary="bold #72f1f5",  # Cyan
    accent="bold #fede5d",  # Retro yellow
    warning="bold #ff9e64",  # Orange
    error="bold #ff5555",  # Red
    success="bold #69ff94",  # Mint green
    dim="#848bbd",  # Muted purple
    bg_dark="#262335",  # Deep purple
    bg_light="#34294f",  # Purple
    text_primary="#ffffff",  # White
    text_secondary="#e8d4f8",  # Light purple
    border_primary="#f97ff5",  # Pink
    border_secondary="#72f1f5",  # Cyan
    code_theme="material",
    gradient_start="#f97ff5",  # Pink
    gradient_end="#72f1f5",  # Cyan
)

# Dracula - Industry Standard
# Classic dark theme beloved by developers worldwide.
DRACULA = Theme(
    name="Dracula",
    description="Industry Standard - The classic dark theme",
    primary="bold #bd93f9",  # Purple
    secondary="bold #8be9fd",  # Cyan
    accent="bold #f8f8f2",  # Foreground
    warning="bold #ffb86c",  # Orange
    error="bold #ff5555",  # Red
    success="bold #50fa7b",  # Green
    dim="#6272a4",  # Comment
    bg_dark="#282a36",  # Background
    bg_light="#44475a",  # Current line
    text_primary="#f8f8f2",  # Foreground
    text_secondary="#6272a4",  # Comment
    border_primary="#bd93f9",  # Purple
    border_secondary="#6272a4",  # Comment
    code_theme="dracula",
)

# Obsidian Void - Minimalist Exclusive
# Deep black, grey, and gold accents. Extreme minimalism.
OBSIDIAN = Theme(
    name="Obsidian",
    description="Minimalist Void - Deep black with gold accents",
    primary="bold #d4af37",  # Gold
    secondary="bold #808080",  # Grey
    accent="bold #c0c0c0",  # Silver
    warning="bold #d4af37",  # Gold
    error="bold #8b0000",  # Dark red
    success="bold #228b22",  # Forest green
    dim="#404040",  # Dark grey
    bg_dark="#0a0a0a",  # Near black
    bg_light="#141414",  # Slightly lighter
    text_primary="#c0c0c0",  # Silver
    text_secondary="#808080",  # Grey
    border_primary="#d4af37",  # Gold
    border_secondary="#404040",  # Dark grey
    code_theme="monokai",
)

# Keep Aurora for backwards compatibility
AURORA = Theme(
    name="Aurora",
    description="Nordic Aurora - Green and ice blue",
    primary="bold #00ff9f",  # Aurora Green
    secondary="bold #00b8ff",  # Ice Blue
    accent="bold #d4fffa",  # Pale Cyan
    warning="bold #ffb86c",  # Soft Orange
    error="bold #ff5555",  # Soft Red
    success="bold #50fa7b",  # Bright Green
    dim="#6272a4",  # Comment grey
    bg_dark="#0d1117",  # Deep Nordic Night
    bg_light="#161b22",  # Slightly lighter
    text_primary="#f8f8f2",  # Off-white
    text_secondary="#8be9fd",  # Cyan Text
    border_primary="#00ff9f",  # Green
    border_secondary="#00b8ff",  # Blue
    code_theme="manni",
)


# =============================================================================
# THEME MANAGEMENT
# =============================================================================

# All available themes
THEMES = {
    "nord": NORD,
    "cyberpunk": CYBERPUNK,
    "synthwave": SYNTHWAVE,
    "dracula": DRACULA,
    "obsidian": OBSIDIAN,
    "aurora": AURORA,  # Legacy
}

# Current active theme (default: Synthwave)
_current_theme: Theme = SYNTHWAVE


def set_theme(name: str) -> Theme:
    """Set the current theme by name.

    Args:
        name: Theme name (nord, cyberpunk, synthwave, dracula, obsidian)

    Returns:
        The activated Theme object

    Raises:
        ValueError: If theme name is not recognized
    """
    global _current_theme

    name = name.lower()
    if name not in THEMES:
        available = ", ".join(THEMES.keys())
        raise ValueError(f"Unknown theme '{name}'. Available: {available}")

    _current_theme = THEMES[name]
    return _current_theme


def get_current_theme() -> Theme:
    """Get the currently active theme."""
    return _current_theme


def get_theme(name: str) -> Theme:
    """Get a theme by name without activating it."""
    name = name.lower()
    if name not in THEMES:
        raise ValueError(f"Unknown theme: {name}")
    return THEMES[name]


def list_themes() -> list[str]:
    """Get list of available theme names."""
    return list(THEMES.keys())


# For backwards compatibility
CURRENT_THEME = _current_theme


# Convenience function to get colors (for modules that import at load time)
def Colors() -> Theme:
    """Get current theme colors. Use this instead of CURRENT_THEME."""
    return _current_theme

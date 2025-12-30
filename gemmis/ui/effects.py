"""
GEMMIS Visual Effects Engine

Provides visual effects for the GEMMIS TUI:
- GlitchOverlay: Full-screen glitch effect
- MatrixSpinner: Matrix-style animated spinner
- PulseBorder: Pulsating border colors
- GlitchText: Text with character corruption
- HexDump: Fake memory hex dump display
- GhostTyper: Ghost typing animation for streaming
- CRTScanlines: Retro CRT scanline overlay
- animate_gradient: Color interpolation utility
"""
import math
import random
import time
from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text

from .theme import get_current_theme


def animate_gradient(color_start: str, color_end: str, progress: float) -> str:
    """Interpolate between two hex colors.

    Args:
        color_start: Start color in hex format (e.g., '#ff00ff')
        color_end: End color in hex format (e.g., '#00ffff')
        progress: Float from 0.0 to 1.0

    Returns:
        Interpolated hex color string
    """
    # Clean colors
    c1 = color_start.lstrip('#').replace('bold ', '')
    c2 = color_end.lstrip('#').replace('bold ', '')

    # Parse RGB
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)

    # Interpolate
    progress = max(0.0, min(1.0, progress))
    r = int(r1 + (r2 - r1) * progress)
    g = int(g1 + (g2 - g1) * progress)
    b = int(b1 + (b2 - b1) * progress)

    return f"#{r:02x}{g:02x}{b:02x}"


class MatrixSpinner:
    """Matrix-style spinner animation for processing states.

    Creates a small box of falling Matrix-style characters.
    """

    CHARS = "日ハミヒーウシナモニサワツオリアホテマケメエカキムユラセネスタヌヘ012345789ABCDEF"

    def __init__(self, width: int = 12, height: int = 3):
        self.width = width
        self.height = height
        self.frame = 0
        self.columns = [random.randint(0, height * 2) for _ in range(width)]

    def render(self) -> Text:
        """Render the spinner animation frame."""
        theme = get_current_theme()
        primary = theme.primary.replace("bold ", "")

        self.frame += 1
        lines = []

        for y in range(self.height):
            line = Text()
            for x in range(self.width):
                col_pos = (self.columns[x] + self.frame // 2) % (self.height * 2)

                if col_pos == y:
                    # Brightest char (head)
                    char = random.choice(self.CHARS)
                    line.append(char, style=f"bold {primary}")
                elif col_pos - 1 == y or col_pos - 2 == y:
                    # Trail
                    char = random.choice(self.CHARS)
                    line.append(char, style=f"dim {primary}")
                else:
                    line.append(" ")
            lines.append(line)

        return Text("\n").join(lines)

    def __rich__(self) -> Text:
        return self.render()


class PulseBorder:
    """Animated pulsing border effect using color interpolation.

    Creates a time-based oscillating brightness for borders.
    """

    @staticmethod
    def get_style(base_color: str, speed: float = 1.0, min_brightness: float = 0.3) -> str:
        """Get the current pulse style based on time.

        Args:
            base_color: Base color in hex format
            speed: Pulse speed multiplier
            min_brightness: Minimum brightness (0.0-1.0)

        Returns:
            Style string with current color
        """
        # Calculate oscillation based on time
        t = time.time() * speed
        # Sine wave oscillation between min_brightness and 1.0
        brightness = min_brightness + (1.0 - min_brightness) * (0.5 + 0.5 * math.sin(t * math.pi))

        # Parse base color
        color = base_color.lstrip('#').replace('bold ', '')
        if len(color) == 6:
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

            # Apply brightness
            r = int(r * brightness)
            g = int(g * brightness)
            b = int(b * brightness)

            return f"#{r:02x}{g:02x}{b:02x}"

        return base_color


class GlitchText:
    """Text with random character glitching effect.

    Reveals text progressively with glitch noise on unrevealed characters.
    """

    GLITCH_CHARS = "░▒▓█▀▄▌▐╳╱╲◢◣◤◥"

    def __init__(self, target_text: str, duration: float = 1.0, glitch_intensity: float = 0.3):
        self.target_text = target_text
        self.duration = duration
        self.glitch_intensity = glitch_intensity
        self.start_time = time.time()

    def render(self) -> Text:
        """Render the glitched text."""
        theme = get_current_theme()
        primary = theme.primary.replace("bold ", "")
        dim = theme.dim

        elapsed = time.time() - self.start_time
        progress = min(1.0, elapsed / self.duration)

        result = Text()
        reveal_index = int(len(self.target_text) * progress)

        for i, char in enumerate(self.target_text):
            if i < reveal_index:
                # Revealed character
                result.append(char, style=f"bold {primary}")
            elif random.random() < self.glitch_intensity:
                # Glitch character
                result.append(random.choice(self.GLITCH_CHARS), style=f"{dim}")
            else:
                # Hidden character
                result.append("█", style=f"dim {dim}")

        return result

    @property
    def complete(self) -> bool:
        """Check if the glitch animation is complete."""
        return (time.time() - self.start_time) >= self.duration

    def __rich__(self) -> Text:
        return self.render()


class HexDump:
    """Fake hex memory dump display for cyberpunk aesthetic.

    Generates realistic-looking hexadecimal memory dumps.
    """

    def __init__(self, lines: int = 4, base_address: int = None, animate: bool = True):
        self.lines = lines
        self.base_address = base_address or random.randint(0x7F000000, 0x7FFFFFFF)
        self.animate = animate
        self.frame = 0

    def render(self) -> Text:
        """Render the hex dump."""
        theme = get_current_theme()
        primary = theme.primary.replace("bold ", "")
        secondary = theme.secondary.replace("bold ", "")
        dim = theme.dim

        self.frame += 1
        result = Text()

        for i in range(self.lines):
            addr = self.base_address + (i * 16)

            # Address
            result.append(f"0x{addr:08X}: ", style=f"dim {dim}")

            # Hex bytes (16 bytes per line)
            for j in range(16):
                if self.animate and random.random() < 0.05:
                    # Occasional "corruption"
                    byte_val = random.randint(0, 255)
                    result.append(f"{byte_val:02X} ", style=f"bold {secondary}")
                else:
                    byte_val = random.randint(0, 255)
                    result.append(f"{byte_val:02X} ", style=f"{primary}")

                if j == 7:
                    result.append(" ")

            if i < self.lines - 1:
                result.append("\n")

        return result

    def __rich__(self) -> Text:
        return self.render()


class GhostTyper:
    """Ghost typing animation for streaming text.

    Creates a "typing" effect with cursor and optional ghost preview.
    """

    CURSOR_CHARS = ["▌", "▐", "█", " "]

    def __init__(self, show_cursor: bool = True, ghost_length: int = 3):
        self.show_cursor = show_cursor
        self.ghost_length = ghost_length
        self.frame = 0
        self.text = ""

    def update(self, text: str) -> None:
        """Update the text content."""
        self.text = text
        self.frame += 1

    def render(self) -> Text:
        """Render the ghost typer output."""
        theme = get_current_theme()
        primary = theme.primary.replace("bold ", "")
        dim = theme.dim

        result = Text()
        result.append(self.text, style=f"{primary}")

        if self.show_cursor:
            cursor = self.CURSOR_CHARS[self.frame % len(self.CURSOR_CHARS)]
            result.append(cursor, style=f"bold {primary}")

        # Ghost preview (placeholder for upcoming chars)
        if self.ghost_length > 0:
            ghost = "".join(random.choice("░▒▓") for _ in range(self.ghost_length))
            result.append(ghost, style=f"dim {dim}")

        return result

    def __rich__(self) -> Text:
        return self.render()


class CRTScanlines(Static):
    """CRT scanline overlay effect for retro aesthetic.

    Creates horizontal scanlines with optional flicker.
    """

    DEFAULT_CSS = """
    CRTScanlines {
        layer: overlay;
        width: 100%;
        height: 100%;
        background: transparent;
    }
    """

    def __init__(self, opacity: float = 0.1, flicker: bool = True):
        super().__init__()
        self.opacity = opacity
        self.flicker = flicker
        self.frame = 0

    def on_mount(self) -> None:
        self.display = False
        if self.flicker:
            self.set_interval(0.1, self.tick)

    def tick(self) -> None:
        if self.display:
            self.frame += 1
            self.refresh()

    def toggle(self) -> None:
        """Toggle scanlines on/off."""
        self.display = not self.display

    def render(self) -> Text:
        if not self.display:
            return Text("")

        width = self.size.width or 80
        height = self.size.height or 24

        lines = []
        for y in range(height):
            if y % 2 == 0:
                # Even lines: transparent (no scanline)
                lines.append(Text(" " * width))
            else:
                # Odd lines: scanline effect
                # Add flicker variation
                if self.flicker and random.random() < 0.02:
                    intensity = random.choice(["#333333", "#222222", "#444444"])
                else:
                    intensity = "#1a1a1a"

                line = Text("─" * width, style=f"dim {intensity}")
                lines.append(line)

        return Text("\n").join(lines)

class ChromaticAberration:
    """RGB split effect for glitch aesthetics.

    Creates a color separation effect where text appears with offset
    red and cyan 'shadows' - simulating CRT color misalignment.
    """

    def __init__(self, offset: int = 1):
        """Initialize chromatic aberration effect.

        Args:
            offset: Character offset for color channels (default 1)
        """
        self.offset = offset

    def apply(self, text: str, intensity: float = 1.0) -> Text:
        """Apply chromatic aberration to text.

        Args:
            text: The text to process
            intensity: Effect intensity (0.0-1.0)

        Returns:
            Rich Text object with RGB split effect
        """
        theme = get_current_theme()
        primary = theme.primary.replace("bold ", "")

        result = Text()
        lines = text.split("\n")

        for line_idx, line in enumerate(lines):
            if not line:
                if line_idx < len(lines) - 1:
                    result.append("\n")
                continue

            # Red channel (shifted left)
            red_offset = " " * max(0, self.offset)
            cyan_offset = " " * max(0, self.offset)

            # Build the line with color separation
            for i, char in enumerate(line):
                if random.random() < intensity * 0.3:
                    # Apply chromatic split on some characters
                    if i > 0:
                        result.append(line[i - 1], style="dim #ff0040")  # Red ghost
                    result.append(char, style=f"bold {primary}")
                    if i < len(line) - 1:
                        result.append(line[i + 1], style="dim #00ffff")  # Cyan ghost
                else:
                    result.append(char, style=primary)

            if line_idx < len(lines) - 1:
                result.append("\n")

        return result

    def render_line(self, text: str) -> Text:
        """Render a single line with RGB offset effect.

        Args:
            text: Single line of text

        Returns:
            Text with horizontal RGB separation
        """
        if not text:
            return Text("")

        result = Text()

        # Red channel (offset left)
        result.append(text[1:] if len(text) > 1 else "", style="dim #ff0040")
        result.append("\n")

        # Main channel
        theme = get_current_theme()
        result.append(text, style=theme.primary.replace("bold ", ""))
        result.append("\n")

        # Cyan channel (offset right)
        result.append(" " + text[:-1] if len(text) > 1 else "", style="dim #00ffff")

        return result


class GlitchOverlay(Static):
    """A full-screen transparent overlay that creates digital glitches."""

    def on_mount(self) -> None:
        self.display = False
        self.set_interval(0.05, self.tick)
        self.glitch_active = False
        self.intensity = 0.1

    def trigger(self, duration: float = 0.5, intensity: float = 0.2):
        """Trigger a temporary glitch."""
        self.intensity = intensity
        self.glitch_active = True
        self.display = True
        self.set_timer(duration, self.stop_glitch)

    def stop_glitch(self):
        self.glitch_active = False
        self.display = False

    def tick(self):
        if self.glitch_active:
            self.refresh()

    def render(self) -> Text:
        if not self.glitch_active:
            return Text("")
            
        width = self.size.width
        height = self.size.height
        if width == 0 or height == 0: return Text("")

        chars = " ░▒▓█01_-"
        lines = []
        for _ in range(height):
            if random.random() < self.intensity:
                # Create a horizontal glitch line
                line = "".join(random.choice(chars) if random.random() < 0.3 else " " for _ in range(width))
                lines.append(Text(line, style="on #00ff00" if random.random() > 0.9 else "magenta"))
            else:
                lines.append(Text(" " * width))
        
        return Text("\n").join(lines)
"""
GEMMIS UI Effects - Visual FX for the terminal interface.
"""
import random
import time
import colorsys
import math
from rich.text import Text
from rich.segment import Segment
from rich.style import Style
from .theme import get_current_theme

class GlitchText:
    """
    Generates text that 'glitches' from random characters into the target text.
    """
    def __init__(self, text: str, duration: float = 0.5):
        self.target_text = text
        self.duration = duration
        self.start_time = time.time()
        self.chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;':,./<>?"

    def render(self) -> Text:
        Colors = get_current_theme()
        elapsed = time.time() - self.start_time
        progress = min(1.0, elapsed / self.duration)
        
        if progress >= 1.0:
            return Text(self.target_text, style=Colors.PRIMARY)

        # Number of characters to reveal based on progress
        reveal_count = int(len(self.target_text) * progress)
        
        result = Text()
        
        # Correct part
        result.append(self.target_text[:reveal_count], style=Colors.PRIMARY)
        
        # Glitch part
        remaining = len(self.target_text) - reveal_count
        for _ in range(remaining):
            char = random.choice(self.chars)
            # Randomize style for glitch effect
            style = random.choice([Colors.SECONDARY, Colors.ACCENT, Colors.DIM, Colors.ERROR])
            result.append(char, style=style)
            
        return result

def animate_gradient(text: str, speed: float = 1.0) -> Text:
    """
    Create a living gradient text that shifts hue over time.
    """
    t = time.time() * speed
    result = Text()
    
    # Base hue from time
    base_hue = (t % 10.0) / 10.0
    
    for i, char in enumerate(text):
        # Shift hue per character for gradient
        hue = (base_hue + (i * 0.05)) % 1.0
        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
        # Convert to hex
        color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        result.append(char, style=f"bold {color}")
        
    return result

class ScanlineOverlay:
    """
    Wraps a renderable and applies a scanline effect (alternating background brightness).
    Note: This is a simplified implementation that forces a style on the content.
    True scanlines in Rich require post-processing Console output which is complex.
    Here we just apply alternating styles if the content supports it (like Text).
    For Panels, it's harder. We'll skip for now or use a simple heuristic.
    """
    def __init__(self, renderable):
        self.renderable = renderable

    def __rich_console__(self, console, options):
        # Render the original content
        yield self.renderable

class GhostTyper:
    """
    Decryption effect for typing text.
    Shows random chars ahead of the real text.
    """
    def __init__(self, target_text: str):
        self.target_text = target_text
        self.current_len = 0
        self.chars = "01xyz!@#&"

    def update(self, new_full_text: str):
        self.target_text = new_full_text
        self.current_len = len(new_full_text)

    def render(self) -> Text:
        Colors = get_current_theme()
        
        # We assume the caller handles the gradual reveal of target_text (streaming).
        # We just add the "ghost" characters at the end.
        
        # Base text
        result = Text(self.target_text, style=Colors.TEXT_PRIMARY)
        
        # Add ghost characters
        # 3-5 random chars
        ghost_len = random.randint(3, 5)
        for _ in range(ghost_len):
            char = random.choice(self.chars)
            # Make them dim or matrix-green/secondary
            result.append(char, style=f"dim {Colors.SECONDARY}")
            
        return result

class MatrixSpinner:
    """
    A vertical stream of changing hex/binary data to simulate 'thinking'.
    """
    def __init__(self, height: int = 5):
        self.height = height
        self.frames = []
        self.last_update = 0
        self.update_interval = 0.08

    def render(self) -> Text:
        Colors = get_current_theme()
        current_time = time.time()
        
        # Only update chars periodically to save CPU/flicker
        if current_time - self.last_update > self.update_interval:
            self.last_update = current_time
            # Generate new random line
            lines = []
            for _ in range(self.height):
                chunk = "".join(random.choice("01XYZ789") for _ in range(24))
                lines.append(chunk)
            self.frames = lines
        
        if not self.frames:
            return Text("PROCESSING...", style=Colors.DIM)

        text = Text()
        for i, line in enumerate(self.frames):
            # Fade effect: bottom lines are brighter
            if i == len(self.frames) - 1:
                style = f"bold {Colors.ACCENT}"
            elif i == len(self.frames) - 2:
                style = Colors.PRIMARY
            else:
                style = Colors.DIM
            
            text.append(f" █ {line} █\n", style=style)
            
        return text

class PulseBorder:
    """
    Helper to get a border color that pulses over time.
    """
    @staticmethod
    def get_style(base_color: str, speed: float = 2.0) -> str:
        # Simple flicker effect based on time
        t = time.time() * speed
        if int(t) % 2 == 0:
            return f"bold {base_color}"
        else:
            return base_color


class HexDump:
    """
    Simulates a hex dump stream for visualizing binary data reading.
    """
    def __init__(self, size: int = 1024):
        self.size = size
        self.chars = "0123456789ABCDEF"
        self.lines = []
        self._generate()
    
    def _generate(self):
        # Generate some random hex lines
        import random
        for i in range(0, min(self.size, 256), 16):
            offset = f"{i:08x}"
            hex_bytes = " ".join(f"{random.choice(self.chars)}{random.choice(self.chars)}" for _ in range(16))
            ascii_repr = "".join(random.choice("................abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(16))
            self.lines.append(f"{offset}  {hex_bytes}  |{ascii_repr}|")

    def render(self, max_lines: int = 10) -> Text:
        Colors = get_current_theme()
        text = Text()
        
        # Scroll effect based on time
        scroll = int(time.time() * 20) % len(self.lines)
        
        visible_lines = self.lines[scroll:] + self.lines[:scroll]
        visible_lines = visible_lines[:max_lines]
        
        for line in visible_lines:
            text.append(line + "\n", style=f"{Colors.SECONDARY} dim")
            
        return text

class ChromaticText:
    """
    Simulates chromatic aberration by randomly shifting colors of characters.
    Since terminal can't do true alpha blending layers, we use jittery colors.
    """
    def __init__(self, text: str):
        self.text = text

    def render(self) -> Text:
        Colors = get_current_theme()
        result = Text()
        
        # Chance to glitch
        glitch_chance = 0.1
        
        for char in self.text:
            if random.random() < glitch_chance:
                # Aberration colors
                style = random.choice(["bold red", "bold green", "bold blue", "cyan", "magenta"])
                result.append(char, style=style)
            else:
                result.append(char, style=Colors.TEXT_PRIMARY)
                
        return result

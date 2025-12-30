"""
GEMMIS Visual Effects Engine
"""
import random
from textual.widgets import Static
from textual.reactive import reactive
from textual.geometry import Offset
from rich.text import Text

class ScanlineOverlay(Static):
    """A full-screen overlay for CRT scanlines."""
    def contains_point(self, offset: Offset) -> bool:
        """Override to ensure mouse events pass through."""
        return False

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

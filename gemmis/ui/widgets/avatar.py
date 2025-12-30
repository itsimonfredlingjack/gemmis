"""
Avatar Widget - The "Ghost in the Shell"
"""

import asyncio
import random
from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from ..boxes import TECH_BOX
from ..theme import get_current_theme

# ASCII ART FRAMES

# Base Face Structure
# Width approx 20-25 chars

FACE_TEMPLATE = """
  ▄██████████████▄
 █▀              ▀█
 █  [EYES_L]   [EYES_R]  █
 █       [NOSE]        █
 █    [MOUTH]     █
 █▄              ▄█
  ▀██████████████▀
"""

# Eye States
EYES_OPEN = (" █ ", " █ ")
EYES_BLINK = (" ▄ ", " ▄ ")
EYES_WIDE = (" ▀ ", " ▀ ")
EYES_SCAN_1 = ("▓▒░", "░▒▓")
EYES_SCAN_2 = ("▒▓▒", "▒▓▒")
EYES_SCAN_3 = ("░▒▓", "▓▒░")
EYES_GLITCH = ("X", "X")
EYES_ANGRY = (" ◣ ", " ◢ ")

# Mouth States
MOUTH_IDLE = "──────"
MOUTH_OPEN = "▄▀▀▀▀▄"
MOUTH_SPEAK_1 = "▄▄  ▄▄"
MOUTH_SPEAK_2 = " ▀▀▀▀ "
MOUTH_SPEAK_3 = "▀▄▄▄▄▀"
MOUTH_SMILE = " ▀▄▄▀ "

class AvatarWidget(Static):
    """
    A reactive robot avatar that responds to app state.
    States: idle, thinking, speaking, error
    """
    
    # Reactive state
    state = reactive("idle")
    
    def __init__(self):
        super().__init__(id="avatar-container")
        self.tick_count = 0
        self.animation_timer = None
        self._current_eyes = EYES_OPEN
        self._current_mouth = MOUTH_IDLE
        self._glitch_active = False

    def on_mount(self) -> None:
        """Start animation loop"""
        # Optimized: 0.2s interval (5 FPS) is sufficient for TUI
        self.animation_timer = self.set_interval(0.2, self.animate)

    def animate(self) -> None:
        """Update visual frame based on state"""
        self.tick_count += 1
        
        # Store previous state to avoid unnecessary repaints
        prev_eyes = self._current_eyes
        prev_mouth = self._current_mouth
        
        # RANDOM MICRO-GLITCH MECHANIC
        # 0.5% chance every tick (adjusted for slower tick rate)
        if random.random() < 0.005:
            self._current_eyes = EYES_GLITCH
            self._current_mouth = random.choice(["[#%&!]", " ERROR", "NO_CARR"])
            self.refresh()
            return
        
        if self.state == "idle":
            # Blink occasionally
            if self.tick_count % 15 == 0: # Adjusted for 0.2s tick
                self._current_eyes = EYES_BLINK
            elif self.tick_count % 15 == 1:
                self._current_eyes = EYES_OPEN
            self._current_mouth = MOUTH_IDLE

        elif self.state == "thinking":
            # Matrix scanning eyes
            cycle = self.tick_count % 3
            if cycle == 0: self._current_eyes = EYES_SCAN_1
            elif cycle == 1: self._current_eyes = EYES_SCAN_2
            elif cycle == 2: self._current_eyes = EYES_SCAN_3
            
            # Mouth straight or muttering
            self._current_mouth = "••••••" if self.tick_count % 4 < 2 else "......"

        elif self.state == "speaking":
            # Eyes active/wide
            self._current_eyes = EYES_WIDE if self.tick_count % 5 == 0 else EYES_OPEN
            
            # Mouth visualizer
            mouths = [MOUTH_SPEAK_1, MOUTH_SPEAK_2, MOUTH_SPEAK_3, MOUTH_OPEN]
            self._current_mouth = random.choice(mouths)

        elif self.state == "error":
            # Glitch effect
            if self.tick_count % 2 == 0:
                self._current_eyes = EYES_GLITCH
                self._current_mouth = "[ERROR]"
            else:
                self._current_eyes = EYES_BLINK
                self._current_mouth = "X____X"

        # Only refresh if visual state changed
        if self._current_eyes != prev_eyes or self._current_mouth != prev_mouth:
            self.refresh()

    def render(self):
        theme = get_current_theme()
        
        # Build the face string
        face = FACE_TEMPLATE
        face = face.replace("[EYES_L]", self._current_eyes[0])
        face = face.replace("[EYES_R]", self._current_eyes[1])
        face = face.replace("[NOSE]", "||") # Simple nose
        face = face.replace("[MOUTH]", self._current_mouth.center(8))
        
        # Determine Color based on state
        color = theme.primary
        if self.state == "thinking":
            color = theme.secondary
        elif self.state == "speaking":
            color = theme.accent
        elif self.state == "error":
            color = theme.error

        # Create Rich Text
        text = Text(face, style=color)
        
        # Add status text below
        status_map = {
            "idle": "SYSTEM ONLINE",
            "thinking": "PROCESSING...",
            "speaking": "TRANSMITTING",
            "error": "SYSTEM FAILURE"
        }
        status = status_map.get(self.state, "UNKNOWN")
        
        # Gradient status if supported (Synthwave)
        status_text = theme.gradient_text(f"[{status}]")
        status_text.justify = "center"
        
        # Combine
        combined = Text.assemble(text, "\n", status_text)

        return Panel(
            Align.center(combined),
            title=f"[{theme.dim}]NEURAL LINK[/]",
            border_style=color,
            box=TECH_BOX,
            padding=(1, 1)
        )

    def set_state(self, new_state: str):
        """Public method to change state"""
        self.state = new_state

"""
GEMMIS Avatar Widget
"""

from textual.app import ComposeResult
from textual.widgets import Static
from textual.reactive import reactive

from .avatar_assets import IDLE_FRAMES, THINKING_FRAMES, SPEAKING_FRAMES, ERROR_FRAME
from ...audio import get_audio

class AvatarWidget(Static):
    """
    Reactive ASCII Robot Avatar
    States: idle, thinking, speaking, error
    """

    state = reactive("idle")
    frame_index = reactive(0)

    def __init__(self):
        super().__init__()
        self.audio = get_audio()
        self.animation_timer = None
        self.audio_timer = None

    def on_mount(self) -> None:
        self.update_animation()
        self.animation_timer = self.set_interval(0.5, self.next_frame)
        self.audio_timer = self.set_interval(0.1, self.play_speaking_sfx) # Fast tick for speaking audio sync?

    def next_frame(self) -> None:
        self.frame_index += 1
        self.refresh_content()

    def play_speaking_sfx(self):
        # Only play if speaking and frame changed recently?
        # Actually simplest is just random probability if speaking
        if self.state == "speaking":
             # We let the main loop trigger token sounds usually,
             # but we can add ambient mechanical sounds here if needed.
             pass

    def watch_state(self, old_state: str, new_state: str) -> None:
        self.frame_index = 0
        self.refresh_content()

        # Adjust animation speed based on state
        if self.animation_timer:
            self.animation_timer.stop()

        if new_state == "idle":
            self.animation_timer = self.set_interval(0.8, self.next_frame) # Slow pulse
        elif new_state == "thinking":
            self.animation_timer = self.set_interval(0.1, self.next_frame) # Fast scan
            self.audio.play("token") # Just one blip on start
        elif new_state == "speaking":
            self.animation_timer = self.set_interval(0.15, self.next_frame) # Lip sync speed
        elif new_state == "error":
            self.animation_timer = self.set_interval(0.2, self.next_frame) # Glitch speed
            self.audio.play("error")

    def refresh_content(self):
        frames = IDLE_FRAMES
        if self.state == "thinking":
            frames = THINKING_FRAMES
        elif self.state == "speaking":
            frames = SPEAKING_FRAMES
        elif self.state == "error":
            frames = [ERROR_FRAME]

        # Loop index
        idx = self.frame_index % len(frames)
        self.update(frames[idx])

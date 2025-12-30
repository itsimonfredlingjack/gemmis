"""
Chat Widgets for Gemmis TUI
"""
import pyperclip
import random
from textual.app import ComposeResult
from textual.widgets import Static, Button, Markdown
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.message import Message
from textual.reactive import reactive

class Chat(Static):
    """The main chat widget, containing the chat display and input."""
    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="chat-display")

    def add_message(self, role: str, content: str):
        """Add a message to the chat display."""
        chat_display = self.query_one("#chat-display")
        chat_display.mount(ChatBubble(role, content))

class CodeBlock(Static):
    """A widget for displaying code blocks with copy/apply buttons."""

    def __init__(self, code: str, language: str = ""):
        super().__init__(classes=language.strip())
        self.code = code
        self.language = language

    def compose(self) -> ComposeResult:
        with Vertical():
            if self.language.strip() != "ascii":
                with Horizontal(classes="code-toolbar"):
                    yield Button("Copy", id="copy")
                    yield Button("Apply", id="apply")
            yield Markdown(f"```{self.language}\n{self.code}\n```", id="code")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy":
            pyperclip.copy(self.code)
            self.notify("Code copied to clipboard.")
        elif event.button.id == "apply":
            from ...tools import write_file
            # This is a simplified approach. A more robust solution would
            # involve a modal to get the filename from the user.
            write_file("applied_code.py", self.code)
            self.notify("Code applied to `applied_code.py`")

class ChatBubble(Static):
    """A chat bubble for displaying a single message with typewriter effect."""
    
    rendered_content = reactive("")

    def __init__(self, role: str, content: str):
        super().__init__(classes=f"chat-bubble {role}")
        self.role = role
        self.full_content = content
        self.current_index = 0
        
        # OMEGA VISUALS: Cyberpunk Prefixes
        prefix = ""
        if role == "user":
            prefix = "▆▅▃ [USER_UPLINK] >> "
        elif role == "assistant":
            prefix = "█▓▒░ [GEMMIS_CORE] >> "
        elif role == "system":
            prefix = "[SYSTEM_LOG] :: "
            
        self.display_content = prefix + content

    def on_mount(self) -> None:
        """Start the typewriter effect if it's the assistant or system"""
        if self.role in ["assistant", "system"]:
            # Fast typewriter for sci-fi feel
            self.set_interval(0.01, self.type_step)
        else:
            self.rendered_content = self.display_content

    def type_step(self) -> None:
        """Step the typewriter effect with decoding glitch"""
        if self.current_index < len(self.display_content):
            # Take a chunk of characters for faster "scanning" feel
            step = random.randint(2, 5)
            self.current_index += step

            # The "decoded" part
            visible_part = self.display_content[:self.current_index]

            # The "encrypted" part (future chars) - show a few random chars
            remaining_len = len(self.display_content) - self.current_index
            glitch_len = min(remaining_len, 5) # show up to 5 glitch chars ahead

            glitch_part = ""
            if glitch_len > 0:
                # Use safe chars to avoid markdown injection
                chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                for _ in range(glitch_len):
                    glitch_part += random.choice(chars)
                glitch_part = f"[dim]{glitch_part}[/]"

            self.rendered_content = visible_part + glitch_part
            self.scroll_visible()
        else:
            self.rendered_content = self.display_content
            # Stop the timer

    def compose(self) -> ComposeResult:
        # Use a container for the markdown to allow dynamic updates
        yield Vertical(id="bubble-content")

    def watch_rendered_content(self, value: str) -> None:
        """Update the rendered content when it changes"""
        try:
            container = self.query_one("#bubble-content")
            for child in container.query("*"):
                child.remove()
            
            parts = value.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    if part.strip():
                        container.mount(Markdown(part))
                else:
                    lines = part.split("\n", 1)
                    lang = lines[0] if lines else ""
                    code = lines[1] if len(lines) > 1 else ""
                    container.mount(CodeBlock(code, lang))
        except Exception:
            pass

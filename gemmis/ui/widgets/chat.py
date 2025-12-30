"""
Chat Widgets for Gemmis TUI
"""
import pyperclip
from textual.app import ComposeResult
from textual.widgets import Static, Button, Markdown
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.message import Message

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
        super().__init__()
        self.code = code
        self.language = language

    def compose(self) -> ComposeResult:
        with Vertical():
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
    """A chat bubble for displaying a single message."""

    def __init__(self, role: str, content: str):
        super().__init__(classes=f"chat-bubble {role}")
        self.role = role
        self.content = content

    def compose(self) -> ComposeResult:
        parts = self.content.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 0:
                if part.strip():
                    yield Markdown(part)
            else:
                lines = part.split("\\n", 1)
                lang = lines[0] if lines else ""
                code = lines[1] if len(lines) > 1 else ""
                yield CodeBlock(code, lang)

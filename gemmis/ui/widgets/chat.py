"""
Chat Widgets - Interactive Chat Interface
"""

from textual.app import ComposeResult
from textual.widgets import Static, Button, Markdown, Input, Label
from textual.containers import Vertical, Horizontal
from textual.message import Message
from textual.screen import ModalScreen

class SaveCodeRequest(Message):
    """Message sent when user wants to save code"""
    def __init__(self, code: str):
        self.code = code
        super().__init__()

class ApplyFileModal(ModalScreen[str]):
    """Modal to ask for filename when saving code"""
    def __init__(self, code: str):
        super().__init__()
        self.code = code
        self.filename_input = Input(placeholder="path/to/file.py")

    def compose(self) -> ComposeResult:
        with Vertical(id="tool-dialog"):
            yield Label("[bold]SAVE CODE TO FILE[/]")
            yield self.filename_input
            with Horizontal():
                yield Button("SAVE", variant="success", id="btn-save")
                yield Button("CANCEL", variant="error", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            path = self.filename_input.value
            if path:
                self.dismiss(path)
        else:
            self.dismiss(None)

class CodeBlock(Vertical):
    """Widget for a code block with actions"""

    def __init__(self, code: str, language: str = ""):
        super().__init__()
        self.code = code
        self.language = language

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("COPY", id="btn-copy", variant="primary")
            yield Button("APPLY", id="btn-apply", variant="success")
            yield Static(f"[{self.language}]", classes="lang-label")

        yield Markdown(f"```{self.language}\n{self.code}\n```")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-copy":
            # Call method on the App (requires App to have copy_to_clipboard)
            if hasattr(self.app, "copy_to_clipboard"):
                self.app.copy_to_clipboard(self.code)
                self.notify("Code copied to clipboard!")
            else:
                self.notify("Clipboard not supported", severity="error")

        elif event.button.id == "btn-apply":
            # Post message to App
            self.post_message(SaveCodeRequest(self.code))


class ChatBubble(Static):
    """A single chat message bubble"""

    def __init__(self, role: str, content: str):
        super().__init__()
        self.role = role
        self.content = content
        self.add_class(role)

    def compose(self) -> ComposeResult:
        parts = self.content.split("```")

        if len(parts) == 1:
            yield Markdown(self.content)
            return

        for i, part in enumerate(parts):
            if i % 2 == 0:
                if part.strip():
                    yield Markdown(part)
            else:
                lines = part.split("\n", 1)
                lang = lines[0].strip() if len(lines) > 0 else ""
                code = lines[1] if len(lines) > 1 else ""
                yield CodeBlock(code, lang)

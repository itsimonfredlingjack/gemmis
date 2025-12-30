"""
Command Palette and Keybinding Help Widgets for GEMMIS

Inspired by VS Code command palette and gaming quick-action menus.
"""
from textual.app import ComposeResult
from textual.widgets import Static, Input, ListView, ListItem, Label
from textual.containers import Vertical, Container
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text

from ..theme import get_current_theme


class CommandSelected(Message):
    """Event sent when a command is selected from palette."""
    def __init__(self, command: str, action: str) -> None:
        super().__init__()
        self.command = command
        self.action = action


class CommandPalette(Static):
    """
    VS Code-style command palette with fuzzy search.

    Press Ctrl+P or Ctrl+K to open, type to filter commands.
    """

    DEFAULT_CSS = """
    CommandPalette {
        layer: overlay;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: none;
        align: center middle;
    }

    CommandPalette.visible {
        display: block;
    }

    #palette-container {
        width: 60;
        max-height: 20;
        background: #0a0a0a;
        border: heavy #f97ff5;
        padding: 1;
    }

    #palette-input {
        width: 100%;
        border: solid #00ffff;
        margin-bottom: 1;
    }

    #palette-list {
        height: auto;
        max-height: 14;
    }

    #palette-list > ListItem {
        padding: 0 1;
    }

    #palette-list > ListItem:hover {
        background: #f97ff5 20%;
    }

    #palette-list > ListItem.-highlight {
        background: #f97ff5;
        color: #0a0a0a;
    }
    """

    # All available commands with (display_name, action, description)
    COMMANDS = [
        ("💬 Chat", "switch_tab('tab-chat')", "Switch to Chat tab"),
        ("📊 Dashboard", "switch_tab('tab-dashboard')", "Switch to Dashboard tab"),
        ("🐳 Docker", "switch_tab('tab-docker')", "Switch to Docker tab"),
        ("🔄 Regenerate", "regenerate", "Regenerate last response"),
        ("🗑️ Clear Chat", "clear_chat", "Clear all messages"),
        ("💾 Export Chat", "export_chat", "Export chat to markdown"),
        ("✨ New Session", "new_session", "Start fresh session"),
        ("🌧️ Matrix Rain", "toggle_matrix", "Toggle Matrix effect"),
        ("⚡ Glitch", "trigger_glitch", "Trigger glitch effect"),
        ("📺 CRT Mode", "toggle_scanlines", "Toggle CRT scanlines"),
        ("❓ Keybindings", "show_keybinds", "Show keyboard shortcuts"),
        ("🚪 Quit", "quit", "Exit GEMMIS"),
    ]

    filter_text = reactive("")

    def compose(self) -> ComposeResult:
        with Container(id="palette-container"):
            yield Input(placeholder="Type command...", id="palette-input")
            yield ListView(id="palette-list")

    def on_mount(self) -> None:
        self._populate_list()

    def _populate_list(self, filter_str: str = "") -> None:
        """Populate command list with optional filter."""
        list_view = self.query_one("#palette-list", ListView)
        list_view.clear()

        filter_lower = filter_str.lower()

        for name, action, desc in self.COMMANDS:
            if filter_lower and filter_lower not in name.lower() and filter_lower not in desc.lower():
                continue

            theme = get_current_theme()
            text = Text()
            text.append(name, style=f"bold {theme.primary.replace('bold ', '')}")
            text.append(f"  {desc}", style=theme.dim)

            list_view.append(ListItem(Label(text), name=action))

    def toggle(self) -> None:
        """Toggle palette visibility."""
        if self.has_class("visible"):
            self.remove_class("visible")
        else:
            self.add_class("visible")
            try:
                input_field = self.query_one("#palette-input", Input)
                input_field.value = ""
                input_field.focus()
                self._populate_list()
            except Exception:
                pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter commands as user types."""
        if event.input.id == "palette-input":
            self._populate_list(event.value)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Execute selected command."""
        if event.item.name:
            action = event.item.name
            self.toggle()  # Hide palette

            # Execute the action on the app
            app = self.app
            if app:
                # Handle parameterized actions
                if "(" in action:
                    # e.g., switch_tab('tab-chat')
                    method_name = action.split("(")[0]
                    param = action.split("'")[1] if "'" in action else action.split("(")[1].rstrip(")")
                    method = getattr(app, f"action_{method_name}", None)
                    if method:
                        method(param)
                else:
                    method = getattr(app, f"action_{action}", None)
                    if method:
                        method()

    def on_key(self, event) -> None:
        """Handle escape to close."""
        if event.key == "escape" and self.has_class("visible"):
            self.toggle()
            event.stop()


class KeybindHelp(Static):
    """
    Cyberpunk-styled keybinding cheatsheet overlay.

    Shows all available keybindings in a categorized view.
    """

    DEFAULT_CSS = """
    KeybindHelp {
        layer: overlay;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.85);
        display: none;
        align: center middle;
    }

    KeybindHelp.visible {
        display: block;
    }

    #help-container {
        width: 70;
        height: auto;
        max-height: 30;
        background: #0a0a0a;
        border: heavy #ff00ff;
        padding: 1 2;
    }

    .help-title {
        text-align: center;
        text-style: bold;
        color: #f97ff5;
        margin-bottom: 1;
    }

    .help-section {
        margin-bottom: 1;
    }

    .help-section-title {
        text-style: bold underline;
        color: #00ffff;
    }

    .help-row {
        height: 1;
    }

    .help-key {
        width: 15;
        color: #ff00ff;
        text-style: bold;
    }

    .help-desc {
        color: #888888;
    }
    """

    KEYBINDINGS = {
        "⚡ CORE": [
            ("Ctrl+Q", "Quit GEMMIS"),
            ("Escape", "Cancel generation"),
            ("Ctrl+P/K", "Command palette"),
            ("F12 / ?", "This help screen"),
        ],
        "📑 NAVIGATION": [
            ("Ctrl+1", "Chat tab"),
            ("Ctrl+2", "Dashboard tab"),
            ("Ctrl+3", "Docker tab"),
        ],
        "💬 CHAT": [
            ("Ctrl+R", "Regenerate response"),
            ("Ctrl+L", "Clear chat"),
            ("Ctrl+E", "Export chat"),
            ("Ctrl+N", "New session"),
        ],
        "🎮 HOTBAR": [
            ("F1", "Quick: Explain code"),
            ("F2", "Quick: Find bugs"),
            ("F3", "Quick: Refactor"),
            ("F4", "Quick: Write tests"),
            ("`", "Toggle: qwen3 ↔ coder"),
        ],
        "✨ EFFECTS": [
            ("Ctrl+M", "Matrix rain"),
            ("Ctrl+G", "Glitch effect"),
            ("Ctrl+S", "CRT scanlines"),
        ],
    }

    def compose(self) -> ComposeResult:
        theme = get_current_theme()
        primary = theme.primary.replace("bold ", "")
        secondary = theme.secondary.replace("bold ", "")
        accent = theme.accent.replace("bold ", "")

        with Container(id="help-container"):
            yield Static(
                Text("╔═══ GEMMIS KEYBINDINGS ═══╗", style=f"bold {primary}"),
                classes="help-title"
            )

            for section_name, bindings in self.KEYBINDINGS.items():
                with Vertical(classes="help-section"):
                    yield Static(
                        Text(section_name, style=f"bold {secondary}"),
                        classes="help-section-title"
                    )
                    for key, desc in bindings:
                        text = Text()
                        text.append(f"  {key:<12}", style=f"bold {accent}")
                        text.append(f" {desc}", style=theme.dim)
                        yield Static(text, classes="help-row")

            yield Static(
                Text("\n[ESC or click to close]", style=f"dim {theme.dim}"),
                classes="help-title"
            )

    def toggle(self) -> None:
        """Toggle help visibility."""
        if self.has_class("visible"):
            self.remove_class("visible")
            self.can_focus = False
        else:
            self.add_class("visible")
            self.can_focus = True
            self.focus()

    def on_blur(self, event) -> None:
        """Close when losing focus."""
        if self.has_class("visible"):
            self.toggle()

    def key_escape(self) -> None:
        """Close on Escape."""
        if self.has_class("visible"):
            self.toggle()

    def on_click(self, event) -> None:
        """Close on click."""
        if self.has_class("visible"):
            self.toggle()

"""
Sidebar Widgets for Gemmis TUI
"""

from textual.app import ComposeResult
from textual.widgets import Static, Label, ListView, ListItem
from textual.containers import Vertical
from textual.reactive import reactive
from textual.message import Message

from ...system_monitor import get_monitor
from ...state import AppState
from ...ollama_client import OllamaClient

class ModelLoaded(Message):
    """Event sent when an Ollama model is selected."""
    def __init__(self, model_name: str) -> None:
        super().__init__()
        self.model_name = model_name

class SystemStats(Static):
    """Displays CPU and RAM usage."""
    cpu_usage = reactive("CPU: 0%")
    ram_usage = reactive("RAM: 0%")

    def __init__(self):
        super().__init__()
        self.monitor = get_monitor()

    def compose(self) -> ComposeResult:
        yield Label("[bold]SYSTEM STATS[/]")
        yield Label(self.cpu_usage, id="cpu-label")
        yield Label(self.ram_usage, id="ram-label")

    def on_mount(self) -> None:
        """Start the CPU polling worker."""
        self.set_interval(1.0, self.poll_stats)

    def poll_stats(self) -> None:
        """Polls system stats and updates reactive properties."""
        cpu = self.monitor.get_cpu_stats().get("usage", 0.0)
        ram = self.monitor.get_memory_stats().get("percent", 0.0)
        self.cpu_usage = f"CPU: {cpu:.1f}%"
        self.ram_usage = f"RAM: {ram:.1f}%"

    def watch_cpu_usage(self, value: str) -> None:
        """Update the CPU label when the reactive property changes."""
        if self.is_mounted:
            self.query_one("#cpu-label", Label).update(value)

    def watch_ram_usage(self, value: str) -> None:
        """Update the RAM label when the reactive property changes."""
        if self.is_mounted:
            self.query_one("#ram-label", Label).update(value)

class OllamaModels(Static):
    """Displays a list of available Ollama models."""
    def __init__(self, client: OllamaClient):
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        yield Label("[bold]OLLAMA MODELS[/]")
        yield ListView(id="model-list")

    async def on_mount(self) -> None:
        """Load the models into the list view."""
        list_view = self.query_one("#model-list", ListView)
        try:
            models = await self.client.get_models()
            for model in models:
                list_view.append(ListItem(Label(model['name']), name=model['name']))
        except Exception as e:
            list_view.append(ListItem(Label(f"Error loading models.")))

    def on_list_view_selected(self, event: ListView.Selected):
        """Handle model selection."""
        if event.item.name:
            self.post_message(ModelLoaded(event.item.name))

class SessionList(Static):
    """Displays a list of chat sessions."""
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state

    def compose(self) -> ComposeResult:
        yield Label("[bold]SESSIONS[/]")
        yield ListView(id="session-list")

    async def on_mount(self) -> None:
        """Load sessions."""
        await self.refresh_sessions()

    async def refresh_sessions(self):
        list_view = self.query_one("#session-list", ListView)
        list_view.clear()
        if self.app_state.use_memory and self.app_state.session_manager:
            try:
                sessions = await self.app_state.session_manager.get_sessions()
                for session in sessions:
                    list_view.append(ListItem(Label(session['name']), name=str(session['id'])))
            except Exception:
                list_view.append(ListItem(Label("Error loading sessions.")))
        else:
            list_view.append(ListItem(Label("Current Session")))


class Sidebar(Vertical):
    """The main sidebar container."""
    def __init__(self, app_state: AppState, client: OllamaClient):
        super().__init__()
        self.app_state = app_state
        self.client = client

    def compose(self) -> ComposeResult:
        yield SystemStats()
        yield OllamaModels(self.client)
        yield SessionList(self.app_state)

"""
<<<<<<< HEAD
Sidebar Widgets - System Monitor and Session List
"""

from textual.app import ComposeResult
from textual.widgets import Static, Sparkline, Label, ListItem, ListView
from textual.containers import Vertical
from textual.reactive import reactive

from ...system_monitor import get_monitor
from ...state import AppState
from .avatar import AvatarWidget

class SystemMonitorWidget(Static):
    """Displays CPU and RAM usage with Sparklines"""

    cpu_usage = reactive(0.0)
    ram_usage = reactive(0.0)

    def __init__(self, state: AppState):
        super().__init__()
        self.state = state
        self.monitor = get_monitor()

    def compose(self) -> ComposeResult:
        yield Label("[bold]SYSTEM VITALS[/]")

        yield Label("CPU Load:")
        yield Sparkline(data=[], summary_function=lambda d: f"{d[-1]:.1f}%" if d else "0%", id="cpu-spark")

        yield Label("RAM Usage:")
        yield Sparkline(data=[], summary_function=lambda d: f"{d[-1]:.1f}%" if d else "0%", id="ram-spark", classes="ram-spark")

    def on_mount(self) -> None:
        self.set_interval(1.0, self.update_stats)

    def update_stats(self) -> None:
        cpu = self.monitor.get_cpu_stats().get("usage", 0.0)
        ram = self.monitor.get_memory_stats().get("percent", 0.0)

        self.query_one("#cpu-spark", Sparkline).data = self.state.cpu_history
        self.query_one("#ram-spark", Sparkline).data = self.state.mem_history

        # Update history in state (although App loop might also do it, let's ensure it here for UI)
        # Note: app.py loop logic handles appending to state history usually.
        # If we replace the loop, we must handle it here or in the main App.
        # We will assume the Main App timer handles updating state, and we just read from it.
        # Actually, for responsiveness, we can push to state here too.

        self.state.cpu_history.append(cpu)
        if len(self.state.cpu_history) > 40:
            self.state.cpu_history.pop(0)

        self.state.mem_history.append(ram)
        if len(self.state.mem_history) > 40:
            self.state.mem_history.pop(0)


class SessionListWidget(Static):
    """Displays list of saved sessions"""

    def compose(self) -> ComposeResult:
        yield Label("[bold]MEMORY BANKS[/]")
        yield ListView(id="session-list")

    async def on_mount(self) -> None:
        await self.refresh_sessions()

    async def refresh_sessions(self):
        list_view = self.query_one("#session-list", ListView)
        list_view.clear()

        # Placeholder for now, as we need access to the store which is in state
        # app.py will inject state.
        # For now, just a static item
        list_view.append(ListItem(Label("Current Session")))

class Sidebar(Vertical):
    """Sidebar container"""
    def __init__(self, state: AppState):
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield AvatarWidget()
        yield SystemMonitorWidget(self.state)
        yield SessionListWidget()
=======
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
>>>>>>> origin/main

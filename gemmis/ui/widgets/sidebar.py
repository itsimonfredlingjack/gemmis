"""
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

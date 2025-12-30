"""
Dashboard Widget for Gemmis TUI
"""
import os
import signal
from textual.app import ComposeResult
from textual.widgets import Static, DataTable, Button, Label
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.message import Message

from ...system_monitor import get_monitor

class ProcessKilled(Message):
    """Event sent when a process is killed."""
    def __init__(self, pid: int) -> None:
        super().__init__()
        self.pid = pid

class KillProcessModal(ModalScreen[bool]):
    """Modal to confirm killing a process."""
    def __init__(self, pid: int, name: str):
        super().__init__()
        self.pid = pid
        self.name = name

    def compose(self) -> ComposeResult:
        with Vertical(id="kill-dialog"):
            yield Label(f"Kill process {self.pid} ({self.name})?")
            with Vertical():
                yield Button("Kill", variant="error", id="kill")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "kill":
            self.dismiss(True)
        else:
            self.dismiss(False)

class Dashboard(Static):
    """A dashboard widget that displays a table of running processes."""

    def __init__(self):
        super().__init__()
        self.monitor = get_monitor()

    def compose(self) -> ComposeResult:
        yield DataTable(id="process-table")

    def on_mount(self) -> None:
        """Set up the table and start refreshing."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("PID", "Name", "CPU %", "Memory (MB)")
        self.set_interval(2.0, self.refresh_table)
        self.refresh_table()

    def refresh_table(self) -> None:
        """Refresh the process table."""
        table = self.query_one(DataTable)
        procs = self.monitor.get_top_processes(limit=20)

        # Preserve cursor position
        cursor_row = table.cursor_row

        table.clear()
        for p in procs:
            table.add_row(p['pid'], p['name'], f"{p['cpu_percent']:.1f}", f"{p['memory_mb']:.1f}", key=str(p['pid']))

        if cursor_row < len(table.rows):
            table.move_cursor(row=cursor_row)


    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle process selection."""
        pid = int(event.row_key.value)
        name = event.table.get_row(event.row_key)[1]

        def handle_kill(kill: bool):
            if kill:
                self.post_message(ProcessKilled(pid))

        self.app.push_screen(KillProcessModal(pid, name), handle_kill)

    def on_process_killed(self, message: ProcessKilled) -> None:
        """Handle the ProcessKilled event."""
        try:
            os.kill(message.pid, signal.SIGKILL)
            self.notify(f"Process {message.pid} killed.")
            self.refresh_table()
        except Exception as e:
            self.notify(f"Error killing process: {e}", severity="error")

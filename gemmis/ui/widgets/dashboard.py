"""
Dashboard Widgets - Process List and Operations
"""

import os
from textual.app import ComposeResult
from textual.widgets import DataTable, Button, Label, Static
from textual.containers import Grid, Vertical
from textual.screen import ModalScreen

from ...system_monitor import get_monitor

class KillProcessModal(ModalScreen[bool]):
    """Modal to confirm process termination"""

    def __init__(self, pid: int, name: str):
        super().__init__()
        self.pid = pid
        self.proc_name = name

    def compose(self) -> ComposeResult:
        with Vertical(id="kill-dialog"):
            yield Label(f"[bold red]⚠ TERMINATE PROCESS?[/]\n\nPID: {self.pid}\nName: {self.proc_name}")
            with Grid(id="dialog-buttons", classes="dialog-grid"):
                yield Button("CONFIRM KILL", variant="error", id="btn-kill")
                yield Button("CANCEL", variant="primary", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-kill":
            self.dismiss(True)
        else:
            self.dismiss(False)


class ProcessList(Static):
    """Process Manager with DataTable"""

    def __init__(self):
        super().__init__()
        self.monitor = get_monitor()

    def compose(self) -> ComposeResult:
        yield DataTable(cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("PID", "Name", "CPU %", "RAM (MB)", "Status")
        self.refresh_processes()
        self.set_interval(2.0, self.refresh_processes)

    def refresh_processes(self) -> None:
        table = self.query_one(DataTable)

        # Save current cursor row
        current_row = table.cursor_row

        # Fetch processes
        procs = self.monitor.get_top_processes(limit=20, sort_by="cpu")

        table.clear()
        for p in procs:
            table.add_row(
                str(p['pid']),
                p['name'],
                f"{p['cpu_percent']:.1f}",
                f"{p['memory_mb']:.0f}",
                p['status'],
                key=str(p['pid']) # Use PID as key
            )

        # Restore cursor if possible
        if current_row is not None and current_row < table.row_count:
             table.move_cursor(row=current_row)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row click"""
        # Get PID from row key
        pid_str = event.row_key.value
        if not pid_str: return

        pid = int(pid_str)
        # Find name (hacky way since we don't store it explicitly in event)
        # We can get it from the cell
        name = self.query_one(DataTable).get_cell(event.row_key, "Name")

        def check_kill(should_kill: bool):
            if should_kill:
                try:
                    os.kill(pid, 9)
                    self.notify(f"Process {pid} terminated.", severity="warning")
                    self.refresh_processes()
                except Exception as e:
                    self.notify(f"Failed to kill {pid}: {e}", severity="error")

        self.app.push_screen(KillProcessModal(pid, name), check_kill)

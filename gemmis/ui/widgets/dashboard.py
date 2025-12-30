"""
Dashboard Widget for Gemmis TUI - GEMINI 3.0 Edition
"""
import os
import signal
from collections import deque
from textual.app import ComposeResult
from textual.widgets import Static, DataTable, Button, Label, Sparkline, ProgressBar
from textual.containers import Vertical, Horizontal, Grid
from textual.screen import ModalScreen
from textual.message import Message
from textual.reactive import reactive

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
            yield Label(f"TERMINATE PROCESS {self.pid} ({self.name})?", classes="bold red")
            with Horizontal(classes="dialog-buttons"):
                yield Button("EXECUTE", variant="error", id="kill")
                yield Button("ABORT", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "kill":
            self.dismiss(True)
        else:
            self.dismiss(False)

class SystemGauge(Static):
    """A futuristic gauge for system metrics"""
    value = reactive(0.0)
    
    def __init__(self, label: str, color: str = "green"):
        super().__init__(classes="gauge-container")
        self.label_text = label
        self.bar_color = color
        self.history = deque([0.0] * 60, maxlen=60)

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="gauge-header"):
                yield Label(self.label_text, classes="gauge-label")
                yield Label("0%", id="gauge-value", classes="gauge-value")
            yield ProgressBar(total=100, show_eta=False, id="gauge-bar", classes=f"gauge-{self.bar_color}")
            yield Sparkline(self.history, summary_function=max, id="gauge-spark")

    def update_val(self, val: float):
        self.value = val
        self.history.append(val)
        
        # Update text
        val_lbl = self.query_one("#gauge-value", Label)
        val_lbl.update(f"{val:.1f}%")
        
        # Update bar
        bar = self.query_one("#gauge-bar", ProgressBar)
        bar.progress = val
        
        # Update sparkline
        spark = self.query_one("#gauge-spark", Sparkline)
        spark.data = list(self.history)

class Dashboard(Static):
    """A dashboard widget that displays system stats and processes."""

    def __init__(self):
        super().__init__()
        self.monitor = get_monitor()

    def compose(self) -> ComposeResult:
        with Grid(id="dashboard-grid"):
            # Top row: Gauges
            with Horizontal(id="gauges-row"):
                yield SystemGauge("CPU CORE", "cyan")
                yield SystemGauge("MEMORY MATRIX", "magenta")
                yield SystemGauge("SWAP BUFFER", "yellow")
            
            # Bottom row: Process Table
            with Vertical(id="process-container"):
                yield Label("ACTIVE PROCESSES [TOP 20]", classes="section-header")
                yield DataTable(id="process-table")

    def on_mount(self) -> None:
        """Set up the table and start refreshing."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("PID", "NAME", "CPU %", "MEM (MB)", "STATUS")
        self.set_interval(1.0, self.refresh_stats) # Faster refresh for smooth graphs
        self.refresh_stats()

    def refresh_stats(self) -> None:
        """Refresh gauges and table."""
        # 1. Update Gauges
        cpu_stats = self.monitor.get_cpu_stats()
        mem_stats = self.monitor.get_memory_stats()
        
        gauges = self.query(SystemGauge)
        if len(gauges) >= 3:
            gauges[0].update_val(cpu_stats.get('percent', 0))
            gauges[1].update_val(mem_stats.get('percent', 0))
            gauges[2].update_val(mem_stats.get('swap_percent', 0))

        # 2. Update Table (less frequently maybe? No, keep it sync)
        table = self.query_one(DataTable)
        procs = self.monitor.get_top_processes(limit=20)

        cursor_row = table.cursor_row
        table.clear()
        
        for p in procs:
            # Fake status for sci-fi feel
            status = "RUNNING" if p['cpu_percent'] > 0 else "IDLE"
            if p['cpu_percent'] > 50: status = "SURGE"
            
            table.add_row(
                p['pid'], 
                p['name'].upper(), 
                f"{p['cpu_percent']:.1f}", 
                f"{p['memory_mb']:.1f}", 
                status,
                key=str(p['pid'])
            )

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
        try:
            os.kill(message.pid, signal.SIGKILL)
            self.notify(f"TARGET {message.pid} NEUTRALIZED.")
            self.refresh_stats()
        except Exception as e:
            self.notify(f"NEUTRALIZATION FAILED: {e}", severity="error")
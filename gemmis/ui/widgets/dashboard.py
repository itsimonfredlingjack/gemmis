"""
Dashboard Widget for Gemmis TUI - GEMINI 3.0 Edition
# Verified OMEGA Update
"""
import asyncio
from collections import deque
from textual.app import ComposeResult
from textual.widgets import Static, Button, Label, Sparkline, ProgressBar
from textual.containers import Vertical, Horizontal, Grid, VerticalScroll
from textual.screen import ModalScreen
from textual.message import Message
from textual.reactive import reactive
from textual import on

from ...system_monitor import get_monitor
from .gpu import GPUGauge

def render_block_bar(percent: float, width: int = 20, theme_color: str = "green") -> str:
    """Renders a '█▓▒░' style progress bar."""
    if width < 1: width = 1
    percent = min(max(percent, 0), 100)
    
    filled_len = int(width * (percent / 100))
    bar = "█" * filled_len
    remainder = (width * (percent / 100)) - filled_len
    if len(bar) < width:
        if remainder > 0.5:
            bar += "▓"
        elif remainder > 0.25:
            bar += "▒"
    
    empty_len = width - len(bar)
    bar += "░" * empty_len
    
    bar = bar[:width]
    
    return f"[{theme_color}]{bar}[/]"

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
        
        val_lbl = self.query_one("#gauge-value", Label)
        val_lbl.update(f"{val:.1f}%")
        
        bar = self.query_one("#gauge-bar", ProgressBar)
        bar.progress = val
        
        spark = self.query_one("#gauge-spark", Sparkline)
        spark.data = list(self.history)

class ProcessSelect(Message):
    """Request to select/kill a process."""
    def __init__(self, pid: int, name: str) -> None:
        super().__init__()
        self.pid = pid
        self.name = name

class ProcessCard(Static):
    """A card representing a single process."""
    
    def __init__(self, proc: dict):
        super().__init__(classes="process-card")
        self.pid = proc.get('pid')
        self.proc_name = proc.get('name')
        self.update_info(proc)
        
    def update_info(self, proc: dict):
        self.cpu = proc.get('cpu_percent', 0)
        self.mem = proc.get('memory_mb', 0)
        
        self.status = "RUNNING"
        if self.cpu > 50: 
            self.status = "SURGE"
            self.add_class("surge")
        else:
            self.remove_class("surge")

        self.update(self._render_content())

    def _render_content(self) -> str:
        cpu_bar = render_block_bar(self.cpu, width=15, theme_color="cyan")
        return (
            f"[bold]{self.proc_name}[/] (PID {self.pid})\n"
            f"CPU: {cpu_bar} {self.cpu:.1f}%\n"
            f"MEM: [magenta]{self.mem:.1f} MB[/]"
        )

    def on_click(self) -> None:
        self.post_message(ProcessSelect(self.pid, self.proc_name))

class Dashboard(Static):
    """A dashboard widget that displays system stats and processes."""

    def __init__(self):
        super().__init__()
        self.monitor = get_monitor()

    def compose(self) -> ComposeResult:
        with Grid(id="dashboard-grid"):
            with Horizontal(id="gauges-row"):
                yield SystemGauge("CPU CORE", "cyan")
                yield SystemGauge("MEMORY MATRIX", "magenta")
                yield GPUGauge()
                yield SystemGauge("SWAP BUFFER", "yellow")
            
            with Vertical(id="process-container"):
                yield Label("ACTIVE PROCESSES [TOP 20]", classes="section-header")
                yield VerticalScroll(id="process-list")

    def on_mount(self) -> None:
        """Start refreshing."""
        self.set_interval(2.0, self.refresh_stats) # Increased interval
        self.run_worker(self.refresh_stats())

    async def refresh_stats(self) -> None:
        """Refresh gauges and process cards asynchronously."""
        # 1. Update Gauges
        cpu_stats, mem_stats, procs = await asyncio.gather(
            self.monitor.get_cpu_stats(),
            self.monitor.get_memory_stats(),
            self.monitor.get_top_processes(limit=20)
        )
        
        try:
            gauges = self.query(SystemGauge)
            if len(gauges) >= 3:
                gauges[0].update_val(cpu_stats.get('usage', 0))
                gauges[1].update_val(mem_stats.get('percent', 0))
                gauges[2].update_val(mem_stats.get('swap_percent', 0))
        except Exception:
            pass # Gauges might not be ready yet

        # 2. Update Processes
        try:
            process_list = self.query_one("#process-list")

            cards = {card.pid: card for card in process_list.query(ProcessCard)}

            # Update existing cards, collect new pids
            new_pids = []
            for p in procs:
                pid = p['pid']
                if pid in cards:
                    cards[pid].update_info(p)
                else:
                    new_pids.append(p)

            # Remove old cards
            proc_pids = {p['pid'] for p in procs}
            for pid, card in cards.items():
                if pid not in proc_pids:
                    await card.remove()

            # Add new cards
            if new_pids:
                await process_list.mount_all([ProcessCard(p) for p in new_pids])
        except Exception:
            pass # Process list might not be ready

    @on(ProcessSelect)
    def on_process_select(self, message: ProcessSelect) -> None:
        """Handle process selection."""
        def handle_kill(kill: bool):
            if kill:
                self.post_message(ProcessKilled(message.pid))

        self.app.push_screen(KillProcessModal(message.pid, message.name), handle_kill)

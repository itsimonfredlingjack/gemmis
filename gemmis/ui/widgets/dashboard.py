"""
Dashboard Widget for Gemmis TUI - GEMINI 3.0 Edition
# Verified OMEGA Update
"""
import os
import signal
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
    # Cap percentage at 100
    percent = min(max(percent, 0), 100)
    
    filled_len = int(width * (percent / 100))
    # Full blocks
    bar = "█" * filled_len
    # Add a 'half' block for precision if needed
    remainder = (width * (percent / 100)) - filled_len
    if len(bar) < width:
        if remainder > 0.5:
            bar += "▓"
        elif remainder > 0.25:
            bar += "▒"
    
    # Fill with empty space or weak blocks
    empty_len = width - len(bar)
    bar += "░" * empty_len
    
    # Truncate if somehow exceeded (shouldn't happen with math above but safety first)
    bar = bar[:width]
    
    return f"[{theme_color}]{bar}[/]"

def render_block_bar(percent: float, width: int = 20, theme_color: str = "green") -> str:
    """Renders a '█▓▒░' style progress bar."""
    if width < 1: width = 1
    # Cap percentage at 100
    percent = min(max(percent, 0), 100)

    filled_len = int(width * (percent / 100))
    # Full blocks
    bar = "█" * filled_len
    # Add a 'half' block for precision if needed
    remainder = (width * (percent / 100)) - filled_len
    if len(bar) < width:
        if remainder > 0.5:
            bar += "▓"
        elif remainder > 0.25:
            bar += "▒"

    # Fill with empty space or weak blocks
    empty_len = width - len(bar)
    bar += "░" * empty_len

    # Truncate if somehow exceeded (shouldn't happen with math above but safety first)
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
        
        # Update text
        val_lbl = self.query_one("#gauge-value", Label)
        val_lbl.update(f"{val:.1f}%")
        
        # Update bar
        bar = self.query_one("#gauge-bar", ProgressBar)
        bar.progress = val
        
        # Update sparkline
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
        self.pid = proc['pid']
        self.proc_name = proc['name']
        self.update_info(proc)
        
    def update_info(self, proc: dict):
        self.cpu = proc['cpu_percent']
        self.mem = proc['memory_mb']
        
        self.status = "RUNNING"
        if self.cpu > 50: 
            self.status = "SURGE"
            self.add_class("surge")
        else:
            self.remove_class("surge")

        # Re-render content
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
            # Top row: Gauges (CPU, Memory, GPU, Swap)
            with Horizontal(id="gauges-row"):
                yield SystemGauge("CPU CORE", "cyan")
                yield SystemGauge("MEMORY MATRIX", "magenta")
                yield GPUGauge()
                yield SystemGauge("SWAP BUFFER", "yellow")
            
            # Bottom row: Process Grid
            with Vertical(id="process-container"):
                yield Label("ACTIVE PROCESSES [TOP 20]", classes="section-header")
                # Use a container for cards that can scroll
                yield VerticalScroll(id="process-list")

    def on_mount(self) -> None:
        """Start refreshing."""
        self.set_interval(1.0, self.refresh_stats)
        self.run_worker(self.refresh_stats())

    async def refresh_stats(self) -> None:
        """Refresh gauges and process cards."""
        # 1. Update Gauges
        cpu_stats = self.monitor.get_cpu_stats()
        mem_stats = self.monitor.get_memory_stats()
        
        gauges = self.query(SystemGauge)
        if len(gauges) >= 3:
            gauges[0].update_val(cpu_stats.get('percent', 0))
            gauges[1].update_val(mem_stats.get('percent', 0))
            gauges[2].update_val(mem_stats.get('swap_percent', 0))

        # 2. Update Processes
        procs = self.monitor.get_top_processes(limit=20)
        
        process_list = self.query_one("#process-list")
        
        # Reuse widget pool
        cards = process_list.query(ProcessCard)
        needed = len(procs)
        existing = len(cards)
        
        # Create more if needed
        if existing < needed:
            for _ in range(needed - existing):
                await process_list.mount(ProcessCard(procs[0])) # Dummy init, will be updated
        
        # Remove excess if needed
        if existing > needed:
            for i in range(needed, existing):
                await cards[i].remove()
        
        # Update content
        cards = process_list.query(ProcessCard)
        for i, p in enumerate(procs):
            if i < len(cards):
                cards[i].pid = p['pid']
                cards[i].proc_name = p['name']
                cards[i].update_info(p)

    @on(ProcessSelect)
    def on_process_select(self, message: ProcessSelect) -> None:
        """Handle process selection."""
        def handle_kill(kill: bool):
            if kill:
                self.post_message(ProcessKilled(message.pid))

        self.app.push_screen(KillProcessModal(message.pid, message.name), handle_kill)

    # Removed local on_process_killed to allow bubbling to App

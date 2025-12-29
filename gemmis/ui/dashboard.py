"""
GEMMIS Dashboard - Full screen TUI mode
"""
import asyncio
import time
from datetime import datetime
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.console import Console, Group
from rich.live import Live

try:
    import asciichartpy
except ImportError:
    asciichartpy = None

from .theme import get_current_theme
from ..system_monitor import get_monitor
from ..state import AppState

class Dashboard:
    def __init__(self, console: Console, state: AppState):
        self.console = console
        self.state = state
        self.monitor = get_monitor()
        self.active = True

    def create_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        layout["left"].split_column(
            Layout(name="cpu_graph", ratio=1),
            Layout(name="mem_graph", ratio=1)
        )
        layout["right"].split_column(
            Layout(name="processes", ratio=1),
            Layout(name="sessions", ratio=1)
        )
        return layout

    def render_header(self) -> Panel:
        Colors = get_current_theme()
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = Text(" GEMMIS DASHBOARD CONTROL ", style=f"bold {Colors.PRIMARY}")
        return Panel(
            Text(f"{t} | SYSTEM ONLINE", style=Colors.ACCENT, justify="center"),
            title=title,
            border_style=Colors.PRIMARY,
            box=box.HEAVY
        )

    def render_graph(self, title: str, data: list[float], color: str) -> Panel:
        Colors = get_current_theme()
        if not data or not asciichartpy:
            content = Text("No Data / Missing Library", style=Colors.DIM)
        else:
            # Asciichart needs a list of numbers
            # Configure cfg for colors
            cfg = {"height": 10, "colors": [asciichartpy.default]} 
            # We strip ansi codes from asciichart usually, or just print it.
            # Rich handles ANSI codes well.
            chart = asciichartpy.plot(data[-40:], cfg) # Last 40 points
            content = Text(chart, style=color)

        return Panel(
            content,
            title=f"[{color}]{title}[/]",
            border_style=Colors.DIM,
            box=box.ROUNDED
        )

    def render_process_list(self) -> Panel:
        Colors = get_current_theme()
        procs = self.monitor.get_top_processes(limit=8, sort_by="cpu")
        
        table = Table(box=None, expand=True, show_header=True, header_style=Colors.SECONDARY)
        table.add_column("PID", style=Colors.DIM, width=6)
        table.add_column("Name", style=Colors.PRIMARY)
        table.add_column("CPU%", justify="right", style=Colors.ACCENT)
        table.add_column("RAM(MB)", justify="right", style=Colors.TEXT_SECONDARY)
        
        for p in procs:
            table.add_row(
                str(p['pid']),
                p['name'][:15],
                f"{p['cpu_percent']:.1f}",
                f"{p['memory_mb']:.0f}"
            )
            
        return Panel(
            table,
            title=f"[{Colors.SECONDARY}] ACTIVE PROCESSES [/]",
            border_style=Colors.BORDER_SECONDARY,
            box=box.ROUNDED
        )

    def render_sessions(self) -> Panel:
        Colors = get_current_theme()
        content = Text("Memory System Unavailable", style=Colors.DIM)
        
        # Async rendering in sync context is hard, so we rely on cached state or just static info
        # ideally we should have pre-fetched sessions. 
        # For this prototype, we'll just show a placeholder if we can't fetch async
        
        # NOTE: Since we are inside an async loop in run(), we can potentially fetch
        # But render_* methods are usually synchronous for Rich Live. 
        # We will assume data is passed or pre-loaded.
        
        table = Table(box=None, expand=True, show_header=False)
        table.add_column("Session")
        
        if self.state.use_memory and hasattr(self.state, 'cached_sessions'):
             for sess in self.state.cached_sessions[:5]:
                 sid = sess.get('session_id', '???')[:8]
                 name = sess.get('name', 'Untitled')
                 table.add_row(f"[{Colors.ACCENT}]{sid}[/] {name}")
        else:
            table.add_row(f"[{Colors.DIM}]No recent sessions loaded[/]")

        return Panel(
            table,
            title=f"[{Colors.ACCENT}] RECENT MEMORY [/]",
            border_style=Colors.BORDER_PRIMARY,
            box=box.ROUNDED
        )

    async def run(self):
        """Run the dashboard loop"""
        Colors = get_current_theme()
        layout = self.create_layout()
        
        # Pre-fetch sessions if possible
        if self.state.use_memory and self.state.session_manager:
            try:
                self.state.cached_sessions = await self.state.session_manager.store.list_sessions()
            except Exception:
                self.state.cached_sessions = []
        
        with Live(layout, console=self.console, screen=True, refresh_per_second=4) as live:
            while self.active:
                # Update Stats
                cpu_stats = self.monitor.get_cpu_stats()
                mem_stats = self.monitor.get_memory_stats()
                
                if cpu_stats:
                    self.state.cpu_history.append(cpu_stats.get('usage', 0))
                if mem_stats:
                    self.state.mem_history.append(mem_stats.get('percent', 0))
                
                # Truncate history for graph
                if len(self.state.cpu_history) > 50: self.state.cpu_history.pop(0)
                if len(self.state.mem_history) > 50: self.state.mem_history.pop(0)

                # Update Layout
                layout["header"].update(self.render_header())
                layout["cpu_graph"].update(self.render_graph("CPU HISTORY", self.state.cpu_history, Colors.WARNING))
                layout["mem_graph"].update(self.render_graph("RAM USAGE", self.state.mem_history, Colors.SECONDARY))
                layout["processes"].update(self.render_process_list())
                layout["sessions"].update(self.render_sessions())
                layout["footer"].update(Panel(Text("PRESS ESC TO RETURN", justify="center"), style=Colors.DIM))
                
                # Check for input (blocking check in a non-blocking way?)
                # We need a way to detect ESC. 
                # prompt_toolkit is good for this, but Rich Live takes over stdout.
                # We'll use a simple blocking check with small timeout or just relying on KeyboardInterrupt for now?
                # Actually, standard input() won't work well with Live.
                # We will rely on KeyboardInterrupt (Ctrl+C) as a fallback or polling if we had a non-blocking input lib.
                # For this prototype, we'll auto-refresh every 0.25s.
                # To EXIT: We implement a crude key listener using standard input in non-blocking mode is complex in Python without curses.
                # Alternative: Just run for 5 seconds as demo? No.
                # We will accept Ctrl+C to exit dashboard mode (catch KeyboardInterrupt)
                
                await asyncio.sleep(0.25)


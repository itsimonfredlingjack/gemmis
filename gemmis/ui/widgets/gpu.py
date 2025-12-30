"""
GPU Monitor Widget for GEMMIS TUI

Real-time NVIDIA GPU monitoring with VRAM, utilization, and temperature display.
"""
import subprocess
from collections import deque
from textual.app import ComposeResult
from textual.widgets import Static, Label, Sparkline, ProgressBar
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive

from ..theme import get_current_theme


def get_gpu_stats() -> dict | None:
    """Get NVIDIA GPU stats via nvidia-smi.

    Returns:
        dict with gpu_util, mem_used, mem_total, temp or None if unavailable
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,name",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 5:
                return {
                    "gpu_util": int(parts[0]),
                    "mem_used": int(parts[1]),
                    "mem_total": int(parts[2]),
                    "temp": int(parts[3]),
                    "name": parts[4].strip(),
                }
    except Exception:
        pass
    return None


def render_block_bar(percent: float, width: int = 20, theme_color: str = "green") -> str:
    """Renders a block-style progress bar."""
    if width < 1:
        width = 1
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

    return f"[{theme_color}]{bar[:width]}[/]"


class GPUGauge(Static):
    """GPU monitoring widget with VRAM, utilization, and temperature.

    Displays real-time GPU stats with sparkline history.
    """

    gpu_util = reactive(0.0)
    vram_used = reactive(0)
    vram_total = reactive(6144)  # Default 6GB for RTX 2060
    temperature = reactive(0)
    gpu_name = reactive("GPU")

    def __init__(self):
        super().__init__(classes="gauge-container")
        self.vram_history = deque([0.0] * 60, maxlen=60)
        self.util_history = deque([0.0] * 60, maxlen=60)

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(classes="gauge-header"):
                yield Label("GPU ACCELERATOR", classes="gauge-label")
                yield Label("0%", id="gpu-util-value", classes="gauge-value")
            yield ProgressBar(total=100, show_eta=False, id="gpu-bar", classes="gauge-magenta")
            yield Sparkline(list(self.util_history), summary_function=max, id="gpu-spark")
            with Horizontal(classes="gpu-stats-row"):
                yield Label("VRAM: 0/0 GB", id="vram-label")
                yield Label("TEMP: 0°C", id="temp-label")

    def on_mount(self) -> None:
        """Start GPU polling on mount."""
        self.set_interval(1.0, self.poll_gpu)
        # Initial poll
        self.poll_gpu()

    def poll_gpu(self) -> None:
        """Poll GPU stats and update display."""
        stats = get_gpu_stats()

        if stats:
            self.gpu_util = stats.get("gpu_util", 0)
            self.vram_used = stats.get("mem_used", 0)
            self.vram_total = stats.get("mem_total", 6144)
            self.temperature = stats.get("temp", 0)
            self.gpu_name = stats.get("name", "GPU")

            # Update history
            self.util_history.append(self.gpu_util)
            vram_percent = (self.vram_used / max(self.vram_total, 1)) * 100
            self.vram_history.append(vram_percent)

            self._update_display()
            self._update_warning_state()

    def _update_display(self) -> None:
        """Update all display elements."""
        theme = get_current_theme()

        # Update utilization value
        try:
            util_label = self.query_one("#gpu-util-value", Label)
            util_label.update(f"{self.gpu_util:.0f}%")
        except Exception:
            pass

        # Update progress bar
        try:
            bar = self.query_one("#gpu-bar", ProgressBar)
            bar.progress = self.gpu_util
        except Exception:
            pass

        # Update sparkline
        try:
            spark = self.query_one("#gpu-spark", Sparkline)
            spark.data = list(self.util_history)
        except Exception:
            pass

        # Update VRAM label
        try:
            vram_label = self.query_one("#vram-label", Label)
            vram_gb = self.vram_used / 1024
            total_gb = self.vram_total / 1024
            vram_label.update(f"VRAM: {vram_gb:.1f}/{total_gb:.0f} GB")
        except Exception:
            pass

        # Update temperature label
        try:
            temp_label = self.query_one("#temp-label", Label)
            temp_color = self._get_temp_color()
            temp_label.update(f"[{temp_color}]TEMP: {self.temperature}°C[/]")
        except Exception:
            pass

    def _get_temp_color(self) -> str:
        """Get color based on temperature thresholds."""
        theme = get_current_theme()
        if self.temperature >= 80:
            return theme.error.replace("bold ", "")
        elif self.temperature >= 70:
            return theme.warning.replace("bold ", "")
        else:
            return theme.success.replace("bold ", "")

    def _update_warning_state(self) -> None:
        """Update CSS classes based on GPU state."""
        # Remove existing states
        self.remove_class("gpu-warning")
        self.remove_class("gpu-critical")

        # Add appropriate state
        if self.gpu_util >= 90 or self.temperature >= 80:
            self.add_class("gpu-critical")
        elif self.gpu_util >= 70 or self.temperature >= 70:
            self.add_class("gpu-warning")


class GPUMiniStats(Static):
    """Compact GPU stats for sidebar display."""

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label("GPU: --", id="gpu-mini-label")

    def on_mount(self) -> None:
        self.set_interval(2.0, self.update_stats)
        self.update_stats()

    def update_stats(self) -> None:
        stats = get_gpu_stats()
        if stats:
            theme = get_current_theme()
            util = stats.get("gpu_util", 0)
            temp = stats.get("temp", 0)
            vram_used = stats.get("mem_used", 0) / 1024

            # Color based on utilization
            if util >= 80:
                color = theme.error.replace("bold ", "")
            elif util >= 50:
                color = theme.warning.replace("bold ", "")
            else:
                color = theme.success.replace("bold ", "")

            bar = render_block_bar(util, width=8, theme_color=color)

            try:
                label = self.query_one("#gpu-mini-label", Label)
                label.update(f"GPU: {bar} {util}% | {vram_used:.1f}GB | {temp}°C")
            except Exception:
                pass
        else:
            try:
                label = self.query_one("#gpu-mini-label", Label)
                label.update("GPU: [dim]N/A[/]")
            except Exception:
                pass

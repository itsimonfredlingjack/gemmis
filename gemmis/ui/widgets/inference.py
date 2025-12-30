"""
Inference Stats Widget for GEMMIS TUI

Displays real-time inference statistics: tokens/sec, context usage, model info.
"""
from collections import deque
from textual.app import ComposeResult
from textual.widgets import Static, Label, Sparkline, ProgressBar
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive

from ..theme import get_current_theme


def render_mini_bar(percent: float, width: int = 10, color: str = "cyan") -> str:
    """Render a compact progress bar."""
    percent = min(max(percent, 0), 100)
    filled = int(width * (percent / 100))
    bar = "█" * filled + "░" * (width - filled)
    return f"[{color}]{bar}[/]"


class InferenceStats(Static):
    """Real-time inference statistics widget.

    Shows tokens/sec, context window usage, and generation status.
    """

    tokens_per_sec = reactive(0.0)
    total_tokens = reactive(0)
    context_used = reactive(0)
    context_max = reactive(8192)
    is_generating = reactive(False)

    def __init__(self):
        super().__init__()
        self.tps_history = deque([0.0] * 30, maxlen=30)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("INFERENCE CORE", classes="section-header")
            with Horizontal(classes="inference-row"):
                yield Label("T/s:", classes="dim")
                yield Label("0.0", id="tps-value")
            yield Sparkline(list(self.tps_history), summary_function=max, id="tps-spark")
            yield Label("CTX: 0/8192", id="context-label", classes="dim")
            yield ProgressBar(total=100, show_eta=False, id="context-bar")

    def update_stats(
        self,
        tokens_per_sec: float = None,
        total_tokens: int = None,
        context_used: int = None,
        context_max: int = None,
        is_generating: bool = None,
    ) -> None:
        """Update inference statistics."""
        if tokens_per_sec is not None:
            self.tokens_per_sec = tokens_per_sec
            self.tps_history.append(tokens_per_sec)

        if total_tokens is not None:
            self.total_tokens = total_tokens

        if context_used is not None:
            self.context_used = context_used

        if context_max is not None:
            self.context_max = context_max

        if is_generating is not None:
            self.is_generating = is_generating

        self._update_display()

    def _update_display(self) -> None:
        """Update all display elements."""
        theme = get_current_theme()
        primary = theme.primary.replace("bold ", "")
        secondary = theme.secondary.replace("bold ", "")
        warning = theme.warning.replace("bold ", "")

        # Update T/s value with color coding
        try:
            tps_label = self.query_one("#tps-value", Label)
            if self.tokens_per_sec >= 30:
                color = theme.success.replace("bold ", "")
            elif self.tokens_per_sec >= 15:
                color = primary
            elif self.tokens_per_sec > 0:
                color = warning
            else:
                color = theme.dim

            status = " ▌" if self.is_generating else ""
            tps_label.update(f"[{color}]{self.tokens_per_sec:.1f}{status}[/]")
        except Exception:
            pass

        # Update sparkline
        try:
            spark = self.query_one("#tps-spark", Sparkline)
            spark.data = list(self.tps_history)
        except Exception:
            pass

        # Update context label
        try:
            ctx_label = self.query_one("#context-label", Label)
            ctx_percent = (self.context_used / max(self.context_max, 1)) * 100

            if ctx_percent >= 90:
                color = theme.error.replace("bold ", "")
            elif ctx_percent >= 70:
                color = warning
            else:
                color = theme.dim

            ctx_label.update(f"[{color}]CTX: {self.context_used}/{self.context_max}[/]")
        except Exception:
            pass

        # Update context bar
        try:
            ctx_bar = self.query_one("#context-bar", ProgressBar)
            ctx_percent = (self.context_used / max(self.context_max, 1)) * 100
            ctx_bar.progress = ctx_percent
        except Exception:
            pass


class InferenceMini(Static):
    """Compact inference stats for sidebar."""

    def __init__(self):
        super().__init__()
        self.tps = 0.0
        self.generating = False

    def compose(self) -> ComposeResult:
        yield Label("INF: -- t/s", id="inf-mini-label")

    def update(self, tps: float, generating: bool = False) -> None:
        self.tps = tps
        self.generating = generating
        self._refresh_display()

    def _refresh_display(self) -> None:
        theme = get_current_theme()

        try:
            label = self.query_one("#inf-mini-label", Label)

            if self.tps >= 30:
                color = theme.success.replace("bold ", "")
            elif self.tps >= 15:
                color = theme.primary.replace("bold ", "")
            elif self.tps > 0:
                color = theme.warning.replace("bold ", "")
            else:
                color = theme.dim

            cursor = " ▌" if self.generating else ""
            label.update(f"INF: [{color}]{self.tps:.1f} t/s{cursor}[/]")
        except Exception:
            pass

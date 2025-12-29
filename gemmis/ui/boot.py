"""
GEMMIS Diagnostic Boot Sequence

A professional, animated boot sequence that:
1. Scans system environment (Python, Ollama, GPU, Memory)
2. Displays real diagnostic information
3. Shows an ASCII logo with theme-appropriate styling
4. Adapts animation to terminal capabilities
"""

import subprocess
import sys
import time

from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .theme import Theme, get_current_theme, get_theme

# ASCII Logo - Large version for boot screen
GEMMIS_LOGO = r"""
   ██████╗ ███████╗███╗   ███╗███╗   ███╗██╗███████╗
  ██╔════╝ ██╔════╝████╗ ████║████╗ ████║██║██╔════╝
  ██║  ███╗█████╗  ██╔████╔██║██╔████╔██║██║███████╗
  ██║   ██║██╔══╝  ██║╚██╔╝██║██║╚██╔╝██║██║╚════██║
  ╚██████╔╝███████╗██║ ╚═╝ ██║██║ ╚═╝ ██║██║███████║
   ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝╚═╝╚══════╝
"""

# Smaller logo for narrow terminals
GEMMIS_LOGO_SMALL = r"""
  ╔═══╗╔═══╗╔╗╔╗╔╗╔╗╔╗╔═══╗
  ║╔══╝║╔══╝║║║║║║║║║║║╔═╗║
  ║║╔═╗║╔══╝║╚╝╚╝║║╚╝╚╝║║╚╝
  ║║╚╗║║╚══╗║╔╗╔╗║║╔╗╔╗║╚═╗
  ║╚═╝║║╔══╝║║║║║║║║║║║╔══╝
  ╚═══╝╚╝   ╚╝╚╝╚╝╚╝╚╝╚╝
"""


def get_python_version() -> str:
    """Get Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def check_ollama() -> tuple[bool, str]:
    """Check if Ollama is running and return connection info."""
    try:
        import httpx

        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return True, f"{len(models)} models loaded"
        return False, "Not responding"
    except Exception:
        return False, "Connection failed"


def check_gpu() -> tuple[bool, str | None]:
    """Check for NVIDIA GPU."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(", ")
            name = parts[0] if parts else "Unknown"
            mem = int(parts[1]) if len(parts) > 1 else 0
            return True, f"{name} ({mem // 1024}GB)"
        return False, None
    except Exception:
        return False, None


def get_memory_info() -> str:
    """Get available memory info."""
    try:
        import psutil

        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024**3)
        return f"{available_gb:.1f} GB free"
    except Exception:
        return "Unknown"


def render_boot_panel(
    log_lines: list[tuple[str, bool, str]],
    progress: float,
    theme: Theme,
    show_logo: bool = False,
    console_width: int = 80,
) -> Panel:
    """Render the boot sequence panel."""
    content = Text()

    # Title
    content.append("\n")

    # Show logo if we're at the end
    if show_logo:
        logo = GEMMIS_LOGO if console_width >= 60 else GEMMIS_LOGO_SMALL

        # For Synthwave, use gradient on logo
        if theme.gradient_start and theme.gradient_end:
            for line in logo.strip().split("\n"):
                content.append_text(theme.gradient_text(line))
                content.append("\n")
        else:
            content.append(logo, style=f"bold {theme.primary.replace('bold ', '')}")

        content.append("\n")
        content.append("      [ NEURAL INTERFACE TERMINAL ]\n", style=theme.dim)
    else:
        content.append("  GEMMIS v2.1 DIAGNOSTIC BOOT\n\n", style=f"bold {theme.primary}")

    # Progress bar
    bar_width = min(40, console_width - 10)
    filled = int(bar_width * progress)
    bar = "█" * filled + "░" * (bar_width - filled)
    percent = int(progress * 100)
    content.append(f"  [{theme.primary}]{bar}[/] {percent}%\n\n", style=theme.primary)

    # Log lines
    for step_name, success, detail in log_lines:
        if success is None:
            # Currently checking
            content.append("  [..] ", style=f"bold {theme.warning}")
            content.append(f"{step_name:<25}", style=theme.warning)
            content.append(" checking...\n", style=theme.dim)
        elif success:
            content.append("  [OK] ", style=f"bold {theme.success}")
            content.append(f"{step_name:<25}", style=theme.text_primary)
            content.append(f" {detail}\n", style=theme.dim)
        else:
            content.append("  [!!] ", style=f"bold {theme.error}")
            content.append(f"{step_name:<25}", style=theme.text_primary)
            content.append(f" {detail}\n", style=theme.dim)

    panel_width = min(60, console_width - 4)

    return Panel(
        Align.center(content),
        border_style=theme.border_primary,
        style=f"on {theme.bg_dark}",
        box=box.HEAVY,
        width=panel_width,
        title=f"[{theme.accent}] SYSTEM BOOT [/]",
        padding=(1, 2),
    )


def run_boot_sequence(console: Console, theme: str = "nord") -> None:
    """Run the diagnostic boot sequence.

    Args:
        console: Rich Console instance
        theme: Theme name to use for boot display
    """
    # Get theme (might be different from current theme for preview)
    try:
        boot_theme = get_theme(theme)
    except ValueError:
        boot_theme = get_current_theme()

    console.clear()
    console_width = console.width

    # Boot steps with real checks
    steps = [
        ("Python Environment", lambda: (True, get_python_version())),
        ("Ollama Connection", check_ollama),
        ("GPU Detection", lambda: check_gpu()),
        ("Memory Allocation", lambda: (True, get_memory_info())),
        ("Neural Engine", lambda: (True, "READY")),
    ]

    log_lines: list[tuple[str, bool | None, str]] = []
    hex_chars = "0123456789ABCDEF"

    with Live(
        render_boot_panel(log_lines, 0, boot_theme, False, console_width),
        console=console,
        refresh_per_second=30,
        transient=True,
    ) as live:
        for i, (step_name, check_func) in enumerate(steps):
            # Show "checking..." state
            log_lines.append((step_name, None, ""))
            progress = (i + 0.5) / len(steps)
            live.update(render_boot_panel(log_lines, progress, boot_theme, False, console_width))

            # Quick hex flash effect
            for _ in range(2):
                time.sleep(0.05)

            # Actually run the check
            try:
                success, detail = check_func()
            except Exception as e:
                success, detail = False, str(e)[:20]

            # Update with result
            log_lines[-1] = (step_name, success, detail or "")
            progress = (i + 1) / len(steps)
            live.update(render_boot_panel(log_lines, progress, boot_theme, False, console_width))

            # Brief pause for visual effect
            time.sleep(0.15)

        # Final logo reveal
        time.sleep(0.2)
        live.update(render_boot_panel(log_lines, 1.0, boot_theme, True, console_width))
        time.sleep(0.8)

    # Clear for main app
    console.clear()


def run_boot_sequence_minimal(console: Console) -> None:
    """Run a minimal boot sequence (just a brief flash)."""
    theme = get_current_theme()
    console.print(f"[{theme.primary}]GEMMIS[/] [dim]v2.1[/] - Initializing...", end="\r")
    time.sleep(0.3)
    console.clear()

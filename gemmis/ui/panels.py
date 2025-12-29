"""
GEMMIS UI Panels - GPU monitor, stats, header

Provides real-time system monitoring panels with theme-aware styling.
"""

import subprocess
import colorsys

from rich import box
from rich.panel import Panel
from rich.text import Text
from rich.console import Group

from ..config import MODEL_NAME
from .theme import get_current_theme
from .effects import MatrixSpinner, PulseBorder, GlitchText, HexDump, animate_gradient
from .boxes import TECH_BOX


def _get_avatar_templates() -> dict[str, str]:
    """Get avatar templates with current theme colors."""
    Colors = get_current_theme()

    # Extract color values for avatar markup
    primary = Colors.primary.replace("bold ", "")
    secondary = Colors.secondary.replace("bold ", "")
    warning = Colors.warning.replace("bold ", "")

    return {
        "idle": f"""
 [bold {primary}] ▄▄█████▄▄ [/] 
 [bold {primary}]▐█▀     ▀█▌[/] 
 [bold {primary}]▐█   [/][bold white]◉[/][bold {primary}]   █▌[/] 
 [bold {primary}]▐█▄     ▄█▌[/] 
 [bold {primary}] ▀▀█████▀▀ [/] 
""",
        "thinking": f"""
 [bold {warning}] ▄▄█████▄▄ [/] 
 [bold {warning}]▐█[/][bold white]▀▄▀▄▀▄▀[/][bold {warning}]█▌[/] 
 [bold {warning}]▐█ [/][bold white]⇄[/][bold {warning}]   [/][bold white]⇄[/][bold {warning}] █▌[/] 
 [bold {warning}]▐█[/][bold white]▄▀▄▀▄▀▄[/][bold {warning}]█▌[/] 
 [bold {warning}] ▀▀█████▀▀ [/] 
""",
        "speaking": f"""
 [bold {secondary}] ▄▄█████▄▄ [/] 
 [bold {secondary}]▐█ [/][bold white] ▂▃▅[/][bold {secondary}] █▌[/] 
 [bold {secondary}]▐█ [/][bold white]▅▃▂ [/][bold {secondary}] █▌[/] 
 [bold {secondary}]▐█ [/][bold white] ▂▃▅[/][bold {secondary}] █▌[/] 
 [bold {secondary}] ▀▀█████▀▀ [/] 
""",
    }


def get_avatar(state: str) -> str:
    """Get ASCII avatar for current state with theme colors."""
    avatars = _get_avatar_templates()
    return avatars.get(state, avatars["idle"])


def get_gpu_stats() -> dict:
    """Get NVIDIA GPU stats via nvidia-smi"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 4:
                return {
                    "gpu_util": int(parts[0]),
                    "mem_used": int(parts[1]),
                    "mem_total": int(parts[2]),
                    "temp": int(parts[3]),
                }
    except Exception:
        pass
    return {}


def create_progress_bar(value: int, max_value: int, width: int = 20) -> str:
    """Create a visual progress bar with heatmap colors."""
    Colors = get_current_theme()

    if max_value == 0:
        return "━" * width

    filled_len = int((value / max_value) * width)
    
    # Heatmap logic
    bar_str = ""
    for i in range(width):
        if i < filled_len:
            # Calculate position 0.0 - 1.0
            pos = i / width
            if pos < 0.4:
                color = Colors.PRIMARY
            elif pos < 0.8:
                color = Colors.WARNING
            else:
                color = Colors.ERROR
            bar_str += f"[{color}]█[/]"
        else:
            bar_str += f"[{Colors.DIM}]░[/]"

    return f"{bar_str} [{Colors.ACCENT}]{value}%[/]"


def generate_sparkline(data: list[float], width: int = 20) -> str:
    """Generate a text-based sparkline graph with heatmap coloring."""
    Colors = get_current_theme()

    if not data:
        return " " * width

    # Block characters from empty to full
    bars = "  ▂▃▄▅▆▇█"

    # Ensure we have enough data or pad
    if len(data) < width:
        data = [0.0] * (width - len(data)) + data
    else:
        data = data[-width:]

    line = ""
    for val in data:
        # Normalize 0-100 to 0-8
        idx = int((val / 100.0) * (len(bars) - 1))
        idx = max(0, min(idx, len(bars) - 1))

        # Color based on value intensity (Heatmap)
        if val < 40:
            color = Colors.PRIMARY
        elif val < 80:
            color = Colors.WARNING
        else:
            color = Colors.ERROR

        line += f"[{color}]{bars[idx]}[/]"

    return line


def render_stats_panel(
    connected: bool,
    tokens: int = 0,
    tokens_per_sec: float = 0.0,
    status: str = "READY",
    system_stats: dict = None,
    avatar_state: str = "idle",
    cpu_history: list[float] = None,
    mem_history: list[float] = None,
    tps_history: list[float] = None,
    effects_state: dict = None,
) -> Panel:
    """Render the stats/GPU panel with modern design and system monitoring."""
    Colors = get_current_theme()
    effects_state = effects_state if effects_state is not None else {}

    gpu = get_gpu_stats()
    system_stats = system_stats or {}
    cpu_history = cpu_history or []
    mem_history = mem_history or []
    tps_history = tps_history or []

    content_parts = []

    # 1. AVATAR / BRAIN ACTIVITY / HEX DUMP
    if status == "THINKING":
        # Initialize matrix spinner if needed
        if "matrix" not in effects_state:
            effects_state["matrix"] = MatrixSpinner()
        
        # Render dynamic matrix rain
        content_parts.append(effects_state["matrix"].render())
        content_parts.append(Text("\n"))
    elif "hexdump" in effects_state and effects_state["hexdump"]:
        # Render Hex Dump
        content_parts.append(effects_state["hexdump"].render())
        content_parts.append(Text("\n"))
    else:
        # Standard avatar
        content_parts.append(Text.from_markup(get_avatar(avatar_state)))
        content_parts.append(Text.from_markup("\n"))

    # Status badge
    conn_icon = "●" if connected else "○"
    conn_style = Colors.SUCCESS if connected else Colors.ERROR
    conn_text = "SYSTEM ONLINE" if connected else "SYSTEM OFFLINE"
    content_parts.append(Text.from_markup(f"\n[{conn_style}]{conn_icon} {conn_text}[/]\n"))

    # Model info
    model_display = MODEL_NAME.split(":")[0].upper()
    content_parts.append(
        Text.from_markup(f"[{Colors.DIM}]MODEL CORE:[/] [{Colors.PRIMARY}]{model_display}[/]\n")
    )

    # System stats (CPU, RAM) with Sparklines
    if system_stats:
        cpu = system_stats.get("cpu", {})
        memory = system_stats.get("memory", {})

        if cpu:
            cpu_usage = cpu.get("usage", 0)
            content_parts.append(
                Text.from_markup(
                    f"\n[{Colors.TEXT_SECONDARY}]CPU LOAD[/] [{Colors.ACCENT}]{cpu_usage:.1f}%[/]"
                )
            )
            content_parts.append(Text.from_markup(f"{generate_sparkline(cpu_history, 18)}\n"))

        if memory:
            mem_percent = memory.get("percent", 0)
            mem_used_gb = memory.get("used", 0) / (1024**3)
            mem_total_gb = memory.get("total", 0) / (1024**3)
            content_parts.append(
                Text.from_markup(
                    f"[{Colors.TEXT_SECONDARY}]MEMORY[/] [{Colors.ACCENT}]{mem_percent:.1f}%[/]"
                )
            )
            content_parts.append(Text.from_markup(f"{generate_sparkline(mem_history, 18)}"))
            content_parts.append(
                Text.from_markup(f"[{Colors.DIM}]  {mem_used_gb:.1f}/{mem_total_gb:.1f} GB[/]\n")
            )

    # Token stats (if generating)
    if tokens > 0 or (tps_history and max(tps_history) > 0):
        content_parts.append(
            Text.from_markup(f"\n[{Colors.BORDER_SECONDARY}]────────────────────[/]\n")
        )
        content_parts.append(Text.from_markup(f"[{Colors.TEXT_SECONDARY}]THROUGHPUT[/]"))
        content_parts.append(Text.from_markup(f"[{Colors.ACCENT}]{tokens:,} tok[/]\n"))
        
        # Sparkline for Token Speed
        if tps_history:
             content_parts.append(Text.from_markup(f"{generate_sparkline(tps_history, 18)}"))

        content_parts.append(
            Text.from_markup(
                f"\n[{Colors.DIM}]SPEED:[/] [{Colors.PRIMARY}]{tokens_per_sec:.1f} t/s[/]"
            )
        )

    # Status indicator styling
    status_colors = {
        "READY": Colors.PRIMARY,
        "THINKING": Colors.WARNING,
        "GENERATING": Colors.PRIMARY,
        "DONE": Colors.SUCCESS,
        "ERROR": Colors.ERROR,
    }
    status_color = status_colors.get(status, Colors.DIM)

    # Glitch effect for status text
    if "status_glitch" not in effects_state or effects_state["status_glitch"].target_text != status:
        effects_state["status_glitch"] = GlitchText(status, duration=0.8)
    
    glitch_text = effects_state["status_glitch"].render()
    
    # Dynamic border style
    border_style = Colors.BORDER_PRIMARY
    
    # Use TECH_BOX for that cyber feel
    box_style = TECH_BOX if connected else box.HEAVY
    
    if status == "THINKING":
        border_style = PulseBorder.get_style(Colors.WARNING, speed=5.0)

    content = Group(*content_parts)
    
    # Create title with glitch text
    title_text = Text(" STATUS: ", style=status_color)
    title_text.append(glitch_text)
    title_text.append(" ", style=status_color)

    return Panel(
        content,
        title=title_text,
        border_style=border_style,
        style=f"on {Colors.BG_DARK}",
        box=box_style,
        padding=(1, 2),
    )


def render_header(connected: bool, state: str = "idle") -> Panel:
    """Render header with modern design and theme colors."""
    Colors = get_current_theme()
    avatar = get_avatar(state)

    # State-based styling
    state_styles = {
        "idle": (Colors.PRIMARY, "SYSTEM READY"),
        "thinking": (Colors.WARNING, "PROCESSING..."),
        "speaking": (Colors.SECONDARY, "TRANSMITTING"),
    }
    state_color, state_text = state_styles.get(state, (Colors.PRIMARY, "READY"))

    status_icon = "●" if connected else "○"
    status_color = Colors.SUCCESS if connected else Colors.ERROR
    status_text = "ONLINE" if connected else "OFFLINE"

    # Create header content
    header_content = Text()
    
    # Glow effect for logo (gradient)
    logo_text = animate_gradient(" GEMMIS NEURAL INTERFACE ", speed=2.0)
    header_content.append(logo_text)
    header_content.append("\n")
    
    # We can omit avatar in header since it's in stats panel now to save space
    # header_content.append(Text.from_markup(avatar))
    # header_content.append("\n", style=state_color)
    
    header_content.append(f"  {state_text}", style=f"bold {state_color}")
    header_content.append(f"  [{status_color}]{status_icon} {status_text}[/] ", style=Colors.DIM)

    model_display = MODEL_NAME.split(":")[0].upper()
    header_content.append(f"[{Colors.ACCENT}]│ {model_display}[/]", style=Colors.DIM)

    return Panel(
        header_content,
        border_style=state_color,
        style=f"on {Colors.BG_DARK}",
        box=TECH_BOX if connected else box.HEAVY, # Use Tech Box
        padding=(0, 2),
    )
"""
GEMMIS Setup Wizard - Interactive first-time configuration

A full TUI (Terminal User Interface) for configuring GEMMIS:
1. Environment Check - Scan for Ollama, models, GPU
2. Model Selector - Choose from available models
3. Persona Selection - Pick AI personality
4. Theme Preview - See themes in action
5. Save Configuration
"""

import asyncio

import httpx
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .config import (
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_MODEL_NAME,
    OLLAMA_BASE_URL,
)
from .ui.theme import THEMES, get_theme

console = Console()


async def check_environment() -> dict:
    """Check system environment and return status."""
    status = {
        "ollama_connected": False,
        "models": [],
        "gpu_available": False,
        "gpu_name": None,
        "config_exists": CONFIG_FILE.exists(),
    }

    # Check Ollama connection
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                status["ollama_connected"] = True
                data = response.json()
                status["models"] = [m.get("name", "unknown") for m in data.get("models", [])]
    except Exception:
        pass

    # Check GPU (via nvidia-smi)
    try:
        import subprocess

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            status["gpu_available"] = True
            status["gpu_name"] = result.stdout.strip().split("\n")[0]
    except Exception:
        pass

    return status


def render_environment_check(status: dict, step: int = 0) -> Panel:
    """Render the environment check panel with animated progress."""
    content = Text()
    content.append("SYSTEM INITIALIZATION SEQUENCE\n\n", style="bold cyan")

    checks = [
        ("Python Environment", True, "3.10+"),
        ("Ollama Connection", status.get("ollama_connected", False), OLLAMA_BASE_URL),
        (
            "Available Models",
            len(status.get("models", [])) > 0,
            f"{len(status.get('models', []))} loaded",
        ),
        ("GPU Detected", status.get("gpu_available", False), status.get("gpu_name", "None")),
        ("Config Directory", True, str(CONFIG_DIR)),
    ]

    for i, (name, success, detail) in enumerate(checks):
        if i < step:
            # Completed check
            marker = "[bold green][OK][/bold green]" if success else "[bold red][!!][/bold red]"
            style = "green" if success else "red"
            content.append(f"  {marker} ", style=style)
            content.append(f"{name:<20}", style="bold")
            content.append(f" {detail}\n", style="dim")
        elif i == step:
            # Current check (animated)
            content.append("  [bold yellow][..][/bold yellow] ", style="yellow")
            content.append(f"{name:<20}", style="bold yellow")
            content.append(" checking...\n", style="dim yellow")
        else:
            # Pending check
            content.append("  [dim][  ][/dim] ", style="dim")
            content.append(f"{name:<20}\n", style="dim")

    return Panel(
        content,
        title="[bold cyan] STEP 1/4: Environment Check [/bold cyan]",
        border_style="cyan",
        box=box.HEAVY,
        padding=(1, 2),
    )


def render_model_selector(models: list[str], selected: int = 0) -> Panel:
    """Render the model selection panel."""
    content = Text()
    content.append("SELECT YOUR NEURAL ENGINE\n\n", style="bold cyan")

    if not models:
        content.append("  [yellow]No models found![/yellow]\n")
        content.append("  Install models with: [bold]ollama pull <model>[/bold]\n", style="dim")
    else:
        for i, model in enumerate(models[:10]):  # Show max 10 models
            if i == selected:
                content.append(f"  [bold green]>[/bold green] [bold]{model}[/bold]\n")
            else:
                content.append(f"    {model}\n", style="dim")

        content.append("\n")
        content.append(
            "  Use [bold]↑↓[/bold] to select, [bold]Enter[/bold] to confirm\n", style="dim"
        )

    return Panel(
        content,
        title="[bold cyan] STEP 2/4: Model Selection [/bold cyan]",
        border_style="cyan",
        box=box.HEAVY,
        padding=(1, 2),
    )


def render_theme_preview(theme_name: str) -> Panel:
    """Render a theme preview panel."""
    theme = get_theme(theme_name)

    content = Text()
    content.append("THEME PREVIEW\n\n", style=theme.primary)
    content.append(f"  {theme.name}\n", style=f"bold {theme.primary}")
    content.append(f"  {theme.description}\n\n", style=theme.dim)

    # Show color samples
    content.append("  Primary:   ", style="dim")
    content.append("████████", style=theme.primary)
    content.append("\n")

    content.append("  Secondary: ", style="dim")
    content.append("████████", style=theme.secondary)
    content.append("\n")

    content.append("  Accent:    ", style="dim")
    content.append("████████", style=theme.accent)
    content.append("\n")

    content.append("  Success:   ", style="dim")
    content.append("████████", style=theme.success)
    content.append("\n")

    content.append("  Warning:   ", style="dim")
    content.append("████████", style=theme.warning)
    content.append("\n")

    content.append("  Error:     ", style="dim")
    content.append("████████", style=theme.error)
    content.append("\n")

    # Show gradient if available
    if theme.gradient_start and theme.gradient_end:
        content.append("\n  Gradient:  ", style="dim")
        content.append_text(theme.gradient_text("████████████████"))
        content.append("\n")

    return Panel(
        content,
        border_style=theme.border_primary,
        style=f"on {theme.bg_dark}",
        box=box.HEAVY,
        padding=(1, 2),
    )


async def run_setup_wizard() -> None:
    """Run the interactive setup wizard."""
    console.clear()

    # Step 1: Environment Check
    console.print("\n[bold cyan]GEMMIS SETUP WIZARD[/bold cyan]\n")
    console.print("[dim]Initializing system check...[/dim]\n")

    # Animated environment check
    status = {}
    with Live(render_environment_check(status, 0), console=console, refresh_per_second=10) as live:
        # Check each component with animation
        for step in range(5):
            await asyncio.sleep(0.3)
            if step == 1:
                status = await check_environment()
            live.update(render_environment_check(status, step + 1))

        await asyncio.sleep(0.5)

    console.print()

    # Show results
    if not status.get("ollama_connected"):
        console.print("[bold red]Error:[/bold red] Cannot connect to Ollama")
        console.print(f"[dim]Make sure Ollama is running at {OLLAMA_BASE_URL}[/dim]")
        console.print("[dim]Start with: ollama serve[/dim]\n")
        return

    console.print("[bold green]Environment check passed![/bold green]\n")
    console.print("[dim]Press Enter to continue...[/dim]")
    console.input()

    # Step 2: Model Selection
    console.clear()
    models = status.get("models", [])

    if models:
        console.print(render_model_selector(models, 0))
        console.print(
            f"\n[dim]Enter model number (1-{len(models)}) or press Enter for default:[/dim] ",
            end="",
        )
        choice = console.input().strip()

        if choice.isdigit() and 1 <= int(choice) <= len(models):
            selected_model = models[int(choice) - 1]
        else:
            selected_model = models[0] if models else DEFAULT_MODEL_NAME
    else:
        selected_model = DEFAULT_MODEL_NAME
        console.print(f"[yellow]No models found. Using default: {selected_model}[/yellow]")

    console.print(f"\n[green]Selected model:[/green] [bold]{selected_model}[/bold]\n")

    # Step 3: Theme Selection
    console.print("[bold cyan]STEP 3/4: Theme Selection[/bold cyan]\n")

    theme_names = list(THEMES.keys())
    for i, name in enumerate(theme_names[:5], 1):  # Main 5 themes
        theme = get_theme(name)
        console.print(f"  {i}. [bold]{name}[/bold] - {theme.description}")

    console.print("\n[dim]Enter theme number (1-5) or press Enter for Nord:[/dim] ", end="")
    choice = console.input().strip()

    if choice.isdigit() and 1 <= int(choice) <= 5:
        selected_theme = theme_names[int(choice) - 1]
    else:
        selected_theme = "nord"

    # Show preview
    console.print()
    console.print(render_theme_preview(selected_theme))
    console.print()

    # Step 4: Persona Selection
    console.print("[bold cyan]STEP 4/4: Persona Selection[/bold cyan]\n")

    personas = [
        ("default", "GEMMIS Default", "Helpful, smart, slightly cocky"),
        ("architect", "Software Architect", "Design patterns and best practices"),
        ("hacker", "Elite Hacker", "Terse, efficient, terminal-native"),
        ("assistant", "Friendly Assistant", "Patient, pedagogical, beginner-friendly"),
    ]

    for i, (key, name, desc) in enumerate(personas, 1):
        console.print(f"  {i}. [bold]{name}[/bold] - {desc}")

    console.print("\n[dim]Enter persona number (1-4) or press Enter for default:[/dim] ", end="")
    choice = console.input().strip()

    if choice.isdigit() and 1 <= int(choice) <= 4:
        selected_persona = personas[int(choice) - 1][0]
    else:
        selected_persona = "default"

    # Save configuration
    console.print("\n[bold cyan]Saving configuration...[/bold cyan]")

    config_content = f'''# GEMMIS CLI Configuration
# Generated by setup wizard

[ollama]
base_url = "{OLLAMA_BASE_URL}"

[model]
name = "{selected_model}"
temperature = 0.3
top_p = 0.9
max_tokens = 2048
context_length = 4096

[ui]
theme = "{selected_theme}"
max_history = 50
refresh_rate = 10

[persona]
name = "{selected_persona}"
'''

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config_content)

    console.print(f"[green]Configuration saved to:[/green] {CONFIG_FILE}\n")

    # Final summary
    console.print(
        Panel(
            Text.from_markup(
                f"[bold green]Setup Complete![/bold green]\n\n"
                f"  Model:   [bold]{selected_model}[/bold]\n"
                f"  Theme:   [bold]{selected_theme}[/bold]\n"
                f"  Persona: [bold]{selected_persona}[/bold]\n\n"
                f"[dim]Run [bold]gemmis[/bold] to start chatting![/dim]"
            ),
            title="[bold cyan] INITIALIZATION COMPLETE [/bold cyan]",
            border_style="green",
            box=box.HEAVY,
            padding=(1, 2),
        )
    )

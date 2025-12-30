"""
GEMMIS CLI - Command Line Interface with Typer
"""

import asyncio

import typer
from rich.console import Console

from . import __app_name__, __version__
from .config import (
    CONFIG_FILE,
)

# Create Typer app with rich markup
app = typer.Typer(
    name=__app_name__,
    help="GEMMIS - Neural Interface Terminal for local LLM chat via Ollama",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=False,
)

console = Console()

# Available themes
THEMES = ["nord", "cyberpunk", "synthwave", "dracula", "obsidian"]
DEFAULT_THEME = "synthwave"

# Available personas
PERSONAS = ["default", "architect", "hacker", "assistant"]
DEFAULT_PERSONA = "default"


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold cyan]GEMMIS[/] [dim]v{__version__}[/]")
        console.print("[dim]Neural Interface Terminal for local LLM chat via Ollama[/]")
        raise typer.Exit()


def list_themes_callback(value: bool) -> None:
    """List available themes and exit."""
    if value:
        console.print("\n[bold cyan]Available Themes[/]\n")
        theme_info = {
            "nord": ("Arctic Professional", "Frostbitten blue and snow white"),
            "cyberpunk": ("High-Voltage", "Neon magenta and glowing yellow"),
            "synthwave": ("Retro Future", "Purple to cyan gradients"),
            "dracula": ("Industry Standard", "Classic dark theme"),
            "obsidian": ("Minimalist Void", "Deep black with gold accents"),
        }
        for theme, (title, desc) in theme_info.items():
            marker = "[bold green]>[/]" if theme == DEFAULT_THEME else " "
            console.print(f"  {marker} [bold]{theme}[/] - {title}")
            console.print(f"      [dim]{desc}[/]")
        console.print()
        raise typer.Exit()


def list_personas_callback(value: bool) -> None:
    """List available personas and exit."""
    if value:
        console.print("\n[bold cyan]Available Personas[/]\n")
        persona_info = {
            "default": ("GEMMIS Default", "Helpful, smart, slightly cocky"),
            "architect": ("Software Architect", "Focused on design patterns and best practices"),
            "hacker": ("Elite Hacker", "Terse, efficient, terminal-native"),
            "assistant": ("Friendly Assistant", "Patient, pedagogical, beginner-friendly"),
        }
        for persona, (title, desc) in persona_info.items():
            marker = "[bold green]>[/]" if persona == DEFAULT_PERSONA else " "
            console.print(f"  {marker} [bold]{persona}[/] - {title}")
            console.print(f"      [dim]{desc}[/]")
        console.print()
        raise typer.Exit()


@app.command()
def chat(
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use (e.g., gemma3:4b, qwen2.5:7b)",
    ),
    theme: str = typer.Option(
        DEFAULT_THEME,
        "--theme",
        "-t",
        help="Visual theme (nord, cyberpunk, synthwave, dracula, obsidian)",
    ),
    persona: str = typer.Option(
        DEFAULT_PERSONA,
        "--persona",
        "-p",
        help="AI persona (default, architect, hacker, assistant)",
    ),
    minimal: bool = typer.Option(
        False,
        "--minimal",
        help="Skip boot animation for faster startup",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging",
    ),
    no_screen: bool = typer.Option(
        False,
        "--no-screen",
        help="Disable alternate screen buffer (fixes garbled output in some terminals)",
    ),
    version: bool | None = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    themes: bool | None = typer.Option(
        None,
        "--themes",
        callback=list_themes_callback,
        is_eager=True,
        help="List available themes and exit",
    ),
    personas: bool | None = typer.Option(
        None,
        "--personas",
        callback=list_personas_callback,
        is_eager=True,
        help="List available personas and exit",
    ),
) -> None:
    """
    Start interactive chat session.

    Launch GEMMIS Neural Interface Terminal and begin chatting with your local LLM.

    [bold]Examples:[/]

        gemmis                          # Start with defaults
        gemmis -m qwen2.5:7b            # Use specific model
        gemmis -t synthwave             # Use synthwave theme
        gemmis -p hacker --minimal      # Hacker persona, skip boot
    """
    # Validate theme
    if theme not in THEMES:
        console.print(f"[red]Error:[/] Unknown theme '{theme}'")
        console.print(f"[dim]Available themes: {', '.join(THEMES)}[/]")
        raise typer.Exit(1)

    # Validate persona
    if persona not in PERSONAS:
        console.print(f"[red]Error:[/] Unknown persona '{persona}'")
        console.print(f"[dim]Available personas: {', '.join(PERSONAS)}[/]")
        raise typer.Exit(1)

    # Import here to avoid circular imports and allow CLI to show help fast
    from .app import async_main

    try:
        async_main(
            model=model,
            theme=theme,
            persona=persona,
            minimal=minimal,
            debug=debug,
            no_screen=no_screen,
        )
    except KeyboardInterrupt:
        console.print("\n[dim]Session terminated.[/]")


@app.command()
def setup() -> None:
    """
    Run interactive setup wizard.

    Configure GEMMIS with a guided setup process:
    - Select Ollama model from available models
    - Choose visual theme with live preview
    - Pick AI persona
    - Save preferences to config file
    """
    from .wizard import run_setup_wizard

    try:
        asyncio.run(run_setup_wizard())
    except KeyboardInterrupt:
        console.print("\n[dim]Setup cancelled.[/]")


@app.command()
def config(
    show: bool = typer.Option(
        True,
        "--show",
        "-s",
        help="Show current configuration",
    ),
    path: bool = typer.Option(
        False,
        "--path",
        "-p",
        help="Show config file path only",
    ),
    edit: bool = typer.Option(
        False,
        "--edit",
        "-e",
        help="Open config file in default editor",
    ),
) -> None:
    """
    Show or edit configuration.

    View current settings or open the config file for editing.
    """
    import os
    import subprocess

    if path:
        console.print(str(CONFIG_FILE))
        return

    if edit:
        editor = os.environ.get("EDITOR", "nano")
        if CONFIG_FILE.exists():
            subprocess.run([editor, str(CONFIG_FILE)])
        else:
            console.print("[yellow]Config file not found.[/]")
            console.print("[dim]Run 'gemmis' once to create default config at:[/]")
            console.print(f"  {CONFIG_FILE}")
        return

    # Show config
    console.print("\n[bold cyan]GEMMIS Configuration[/]\n")

    if CONFIG_FILE.exists():
        console.print(f"[dim]Config file:[/] {CONFIG_FILE}\n")
        from .config import CONTEXT_LENGTH, MAX_TOKENS, MODEL_NAME, OLLAMA_BASE_URL, TEMPERATURE

        console.print(f"  [bold]Model:[/]       {MODEL_NAME}")
        console.print(f"  [bold]Temperature:[/] {TEMPERATURE}")
        console.print(f"  [bold]Max Tokens:[/]  {MAX_TOKENS}")
        console.print(f"  [bold]Context:[/]     {CONTEXT_LENGTH}")
        console.print(f"  [bold]Ollama URL:[/]  {OLLAMA_BASE_URL}")
    else:
        console.print("[yellow]No config file found.[/]")
        console.print(f"[dim]Default config will be created at:[/] {CONFIG_FILE}")

    console.print()


@app.command()
def models() -> None:
    """
    List available Ollama models.

    Query Ollama for all installed models and display them.
    """
    import httpx

    from .config import OLLAMA_BASE_URL

    console.print("\n[bold cyan]Available Ollama Models[/]\n")

    try:
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        response.raise_for_status()
        data = response.json()

        models = data.get("models", [])
        if not models:
            console.print("[yellow]No models found.[/]")
            console.print("[dim]Install models with: ollama pull <model>[/]")
            return

        for model in models:
            name = model.get("name", "unknown")
            size = model.get("size", 0) / (1024**3)  # Convert to GB
            console.print(f"  [bold]{name}[/] [dim]({size:.1f} GB)[/]")

        console.print(f"\n[dim]Total: {len(models)} model(s)[/]")

    except httpx.ConnectError:
        console.print("[red]Error:[/] Cannot connect to Ollama")
        console.print(f"[dim]Make sure Ollama is running at {OLLAMA_BASE_URL}[/]")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")

    console.print()


@app.command()
def imagine(
    prompt: str = typer.Argument(..., help="Text description of the image to generate"),
    width: int = typer.Option(60, "--width", "-w", help="Width of ASCII preview in characters"),
) -> None:
    """
    Generate an image from text.

    Uses Pollinations.ai (free) to generate an image and renders an ASCII preview.
    Saves the high-res image to ~/gemmis_images/.
    """
    from .tools import generate_image, image_to_ascii
    import asyncio
    
    with console.status(f"[bold green]Visual Cortex Active...[/] Generating: '{prompt}'"):
        # Since generate_image is sync for now, we run it directly
        result = generate_image(prompt)
    
    if result.get("success"):
        console.print(f"\n[bold green]SUCCESS:[/] Image saved to [underline]{result['filepath']}[/]")
        
        # We need to regenerate ASCII here if we want custom width, or use the one from result
        # The result['ascii'] uses default width (60)
        
        if width != 60:
             # Read file and convert with new width
             try:
                 with open(result['filepath'], "rb") as f:
                     content = f.read()
                 ascii_art = image_to_ascii(content, width=width)
                 console.print(f"\n[bold green]{ascii_art}[/]")
             except Exception:
                 console.print(result.get("ascii", ""))
        else:
            console.print(f"\n[bold green]{result.get('ascii', '')}[/]")
            
        console.print("\n[dim]Use 'xdg-open <filepath>' to view the full resolution image.[/]")
    else:
        console.print(f"\n[bold red]ERROR:[/] {result.get('error', 'Unknown error')}")


# For backwards compatibility, allow running without subcommand
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    model: str | None = typer.Option(None, "--model", "-m", help="Ollama model"),
    theme: str = typer.Option(DEFAULT_THEME, "--theme", "-t", help="Visual theme"),
    persona: str = typer.Option(DEFAULT_PERSONA, "--persona", "-p", help="AI persona"),
    minimal: bool = typer.Option(False, "--minimal", help="Skip boot animation"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug"),
    no_screen: bool = typer.Option(False, "--no-screen", help="Disable alternate screen buffer"),
) -> None:
    """
    GEMMIS - Neural Interface Terminal

    A professional CLI for local LLM chat via Ollama with a stunning visual interface.
    """
    # If no subcommand provided, run chat with provided options
    if ctx.invoked_subcommand is None:
        ctx.invoke(
            chat,
            model=model,
            theme=theme,
            persona=persona,
            minimal=minimal,
            debug=debug,
            no_screen=no_screen,
        )


if __name__ == "__main__":
    app()

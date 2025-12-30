"""
GEMMIS Boot Sequence - Cinematic Intro
"""
import time
import random
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.align import Align
from rich.table import Table

def run_boot_sequence(console: Console, theme: str):
    """
    Execute a cinematic boot sequence before the main app loads.
    """
    
    # 1. Clear screen and show BIOS-like init
    console.clear()
    
    # Fake BIOS check
    console.print("[bold green]GEMMIS NEURAL BIOS v3.0[/]")
    console.print(f"[dim]Copyright (C) 2025 GEMINI CORP. All Rights Reserved.[/]")
    console.print(f"[dim]System Date: {time.strftime('%Y-%m-%d %H:%M:%S')}[/]")
    console.print("[dim]Memory Test: [/]", end="")
    
    for i in range(0, 64000, 4000):
        print(f"\r[dim]Memory Test: {i}K OK[/]", end="")
        time.sleep(0.001)
    console.print("\r[dim]Memory Test: 64000K OK[/]")
    time.sleep(0.2)
    
    boot_checks = [
        "Initializing Neural Core...",
        "Loading Textual UI Engine...",
        "Mounting File System...",
        "Connecting to Ollama Interface...",
        "Calibrating Matrix Rain...",
        "Engaging Audio Cortex...",
        "Establishing Secure Uplink..."
    ]

    for check in boot_checks:
        status = random.choice(["OK", "OK", "OK", "OPTIMIZED"])
        color = "green" if status == "OK" else "cyan"
        console.print(f"  [dim]>[/] {check.ljust(40)} [bold {color}][{status}][/]")
        time.sleep(random.uniform(0.05, 0.2))

    time.sleep(0.5)
    console.clear()

    # 2. The Big Logo Reveal with Progress Bar
    logo_text = """
   ▄██████▄     ▄████████   ▄▄▄▄███▄▄▄▄    ▄▄▄▄███▄▄▄▄    ▄█     ▄████████ 
  ███    ███   ███    ███ ▄██▀▀▀███▀▀▀██▄ ▄██▀▀▀███▀▀▀██▄ ███    ███    ███ 
  ███    █▀    ███    █▀  ███   ███   ███ ███   ███   ███ ███▌   ███    █▀  
 ▄███          ███        ███   ███   ███ ███   ███   ███ ███▌   ███        
▀▀███ ████▄  ▀███████████ ███   ███   ███ ███   ███   ███ ███▌ ▀███████████ 
  ███    ███   ███    ███ ███   ███   ███ ███   ███   ███ ███           ███ 
  ███    ███   ███    ███ ███   ███   ███ ███   ███   ███ ███     ▄█    ███ 
  ████████▀    ███    █▀   ▀█   ███   █▀   ▀█   ███   █▀  █▀    ▄████████▀  
    """

    layout = Layout()
    layout.split_column(
        Layout(name="logo", size=10),
        Layout(name="status", size=3),
        Layout(name="progress", size=3)
    )

    with Live(layout, console=console, refresh_per_second=20):
        # Animate Logo color
        for i in range(20):
            color = "bright_magenta" if i % 2 == 0 else "cyan"
            layout["logo"].update(Align.center(Text(logo_text, style=f"bold {color}")))
            layout["status"].update(Align.center(Text("INITIALIZING NEURAL INTERFACE...", style="dim")))
            time.sleep(0.05)

        # Progress Bar
        total_steps = 100
        for i in range(total_steps + 1):
            time.sleep(0.01)
            
            # Create a manual progress bar using blocks
            bar_width = 40
            filled = int(bar_width * (i / total_steps))
            bar = f"[{'█' * filled}{'░' * (bar_width - filled)}]"
            
            layout["progress"].update(Align.center(
                Text(f"{bar} {i}%", style="bold green")
            ))
            
            if i > 80:
                layout["status"].update(Align.center(Text("DECRYPTING...", style="bold red blinking")))
            elif i > 40:
                layout["status"].update(Align.center(Text("LOADING ASSETS...", style="bold yellow")))

    # Final Flash
    console.clear()
    console.print(Align.center(Text("ACCESS GRANTED", style="bold white on green")))
    time.sleep(0.5)
    console.clear()
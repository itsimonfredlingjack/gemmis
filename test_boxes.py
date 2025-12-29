#!/usr/bin/env python3
"""
Test script for GEMMIS custom box styles
"""

from rich.console import Console
from rich.panel import Panel
from gemmis.ui.boxes import (
    CIRCUIT_BOX,
    TECH_BOX,
    NEON_BOX,
    DATA_BUS_BOX,
    CYBER_GRID_BOX,
)

console = Console()

boxes = [
    ("CIRCUIT_BOX", CIRCUIT_BOX, "Main style with circuit connectors"),
    ("TECH_BOX", TECH_BOX, "Simpler technical look"),
    ("NEON_BOX", NEON_BOX, "Minimal neon aesthetic"),
    ("DATA_BUS_BOX", DATA_BUS_BOX, "Heavy data bus traces"),
    ("CYBER_GRID_BOX", CYBER_GRID_BOX, "Grid-like cyberpunk style"),
]

console.print("\n[bold cyan]GEMMIS Custom Box Styles[/bold cyan]\n")

for name, box, description in boxes:
    panel = Panel(
        f"[yellow]{description}[/yellow]\n\nThis is sample text to show\nhow the box renders with\nmultiple lines of content.",
        title=f"[bold green]{name}[/bold green]",
        box=box,
        padding=(1, 2),
    )
    console.print(panel)
    console.print()

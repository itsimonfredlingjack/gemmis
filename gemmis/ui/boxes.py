"""
GEMMIS UI Boxes - Custom cyberpunk circuitry border styles

Custom Rich.Box styles with tech/circuit aesthetic using Unicode box-drawing
and technical characters for a cyberpunk look.

Box format requires exactly 8 lines of 4 characters each:
  Line 1: top        (left, horizontal, divider, right)
  Line 2: head row   (left, space, vertical, right)
  Line 3: head sep   (left, horizontal, cross, right)
  Line 4: mid row    (left, space, vertical, right)
  Line 5: row sep    (left, horizontal, cross, right)
  Line 6: foot sep   (left, horizontal, cross, right)
  Line 7: foot row   (left, space, vertical, right)
  Line 8: bottom     (left, horizontal, divider, right)
"""

from rich.box import Box

# Circuit Box - Main style with circuit board connectors
CIRCUIT_BOX = Box(
    "╔═╤╗\n"
    "║ │║\n"
    "╟─┼╢\n"
    "║ │║\n"
    "╟─┼╢\n"
    "╟─┼╢\n"
    "║ │║\n"
    "╚═╧╝\n"
)

# Tech Box - Lighter connectors for subtle appearance
TECH_BOX = Box(
    "╒═╤╕\n"
    "│ ││\n"
    "╞═╪╡\n"
    "│ ││\n"
    "╞═╪╡\n"
    "╞═╪╡\n"
    "│ ││\n"
    "╘═╧╛\n"
)

# Neon Box - Minimal single-line aesthetic
NEON_BOX = Box(
    "┌─┬┐\n"
    "│ ││\n"
    "├─┼┤\n"
    "│ ││\n"
    "├─┼┤\n"
    "├─┼┤\n"
    "│ ││\n"
    "└─┴┘\n"
)

# Data Bus Box - Heavy double lines
DATA_BUS_BOX = Box(
    "╔═╦╗\n"
    "║ ║║\n"
    "╠═╬╣\n"
    "║ ║║\n"
    "╠═╬╣\n"
    "╠═╬╣\n"
    "║ ║║\n"
    "╚═╩╝\n"
)

# Cyber Grid Box - Block elements for grid aesthetic
CYBER_GRID_BOX = Box(
    "▛▀▀▜\n"
    "▌ │▐\n"
    "▌─┼▐\n"
    "▌ │▐\n"
    "▌─┼▐\n"
    "▌─┼▐\n"
    "▌ │▐\n"
    "▙▄▄▟\n"
)

__all__ = [
    "CIRCUIT_BOX",
    "TECH_BOX",
    "NEON_BOX",
    "DATA_BUS_BOX",
    "CYBER_GRID_BOX",
    "CYBER_BOX",
    "SCAN_BOX",
]

# Cyber Box - Heavy industrial frame
CYBER_BOX = Box(
    "█▀▀█\n"
    "█  █\n"
    "█──█\n"
    "█  █\n"
    "█──█\n"
    "█──█\n"
    "█  █\n"
    "█▄▄█\n"
)

# Scan Box - Thin scanline frame
SCAN_BOX = Box(
    "╓──╖\n"
    "║  ║\n"
    "╟──╢\n"
    "║  ║\n"
    "╟──╢\n"
    "╟──╢\n"
    "║  ║\n"
    "╙──╜\n"
)

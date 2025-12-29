"""
GEMMIS UI Components

Theme-aware terminal interface components for the GEMMIS CLI.
"""

from .theme import (
    THEMES,
    Theme,
    get_current_theme,
    get_theme,
    list_themes,
    set_theme,
)

from .boxes import (
    CIRCUIT_BOX,
    TECH_BOX,
    NEON_BOX,
    DATA_BUS_BOX,
    CYBER_GRID_BOX,
)

__all__ = [
    "Theme",
    "THEMES",
    "set_theme",
    "get_theme",
    "get_current_theme",
    "list_themes",
    "CIRCUIT_BOX",
    "TECH_BOX",
    "NEON_BOX",
    "DATA_BUS_BOX",
    "CYBER_GRID_BOX",
]

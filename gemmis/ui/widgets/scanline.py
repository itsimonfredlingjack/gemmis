"""
Scanline Overlay Widget for Gemmis
"""
from textual.widgets import Static

class ScanlineOverlay(Static):
    """
    A full-screen overlay that adds a scanline effect.
    Override contains_point to allow clicks to pass through.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = False

    def contains_point(self, point) -> bool:
        """
        Always return False to allow events to pass through to widgets below.
        This simulates 'pointer-events: none'.
        """
        return False

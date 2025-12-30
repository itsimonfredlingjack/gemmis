"""
Particle Effects Widget for Gemmis
"""
import random
from textual.widget import Widget
from textual.reactive import reactive

class Particle(Widget):
    """A single particle that falls and fades."""
    
    char = reactive("*")
    x = reactive(0)
    y = reactive(0)
    
    def __init__(self, x: int, y: int, char: str = "*", color: str = "white"):
        super().__init__()
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.styles.offset = (x, y)
        self.styles.color = color
        self.styles.width = 1
        self.styles.height = 1
        # self.styles.layer = "overlay" # Inherited from parent usually if parent is in overlay

    def render(self) -> str:
        return self.char

    def on_mount(self) -> None:
        # Start animation
        self.set_interval(0.1, self.animate)

    def animate(self) -> None:
        # Move down and maybe side
        self.y += 1
        self.x += random.randint(-1, 1)
        self.styles.offset = (self.x, self.y)
        
        # Chance to die (reduced to make them fall longer)
        if random.random() < 0.05 or self.y > 50: 
            self.remove()

class ParticleSystem(Widget):
    """Container for particles."""
    
    DEFAULT_CSS = """
    ParticleSystem {
        width: 100%;
        height: 100%;
        dock: top;
        layer: overlay;
        background: transparent;
        display: none; /* Hidden by default to not block clicks */
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = False

    def on_mount(self) -> None:
        self.set_interval(0.5, self.check_visibility)

    def check_visibility(self) -> None:
        """Hide system if no particles are active."""
        if not self.children:
            self.styles.display = "none"

    def explode(self, x: int, y: int, count: int = 10, color: str = "yellow"):
        """Spawn an explosion of particles at x, y."""
        self.styles.display = "block" # Enable overlay
        
        chars = ["*", ".", "+", "°", "x"]
        for _ in range(count):
            char = random.choice(chars)
            # Random initial spread
            px = x + random.randint(-2, 2)
            py = y + random.randint(-1, 1)
            self.mount(Particle(px, py, char, color))

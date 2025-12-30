"""
Matrix Rain Widget - Cyberpunk Screensaver
"""
import random
from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style

class MatrixRain(Static):
    """
    A full-screen Matrix digital rain effect.
    """
    
    def __init__(self):
        super().__init__(id="matrix-rain")
        self.columns = []
        self.chars = "日ABDHJIKLMNOPRSTUVWXYZ0123456789$+-*/=%\"'#&_(),.;:?!"
        self.tick_count = 0

    def on_mount(self) -> None:
        """Initialize columns and start animation"""
        self.update_columns()
        # Optimized: 0.2s is enough for a screen saver
        self.set_interval(0.2, self.animate)

    def update_columns(self):
        """Calculate columns based on terminal width"""
        width = self.size.width or 80
        if width < 10: width = 80
        # Each column tracks [y_pos, speed, length]
        self.columns = []
        for _ in range(width):
            self.columns.append({
                "y": random.randint(-20, 0),
                "speed": random.uniform(0.3, 1.0),
                "length": random.randint(5, 15),
            })

    def animate(self) -> None:
        """Step the animation"""
        if not self.display:
            return
            
        self.tick_count += 1
        height = self.size.height or 24
        if height < 5: height = 24
        
        for col in self.columns:
            col["y"] += col["speed"]
            if col["y"] - col["length"] > height:
                col["y"] = random.randint(-10, 0)
                col["speed"] = random.uniform(0.3, 1.0)
                col["length"] = random.randint(5, 15)

        self.refresh()

    def render(self) -> Text:
        if not self.display:
            return Text("")

        width = self.size.width or 80
        height = self.size.height or 24
        
        # Pre-generate characters for all columns to avoid repeated random calls
        chars = [random.choice(self.chars) for _ in range(width * height)]
        
        full_text = Text()
        for y in range(height):
            for x in range(width):
                col = self.columns[x] if x < len(self.columns) else None
                if not col:
                    full_text.append(" ")
                    continue
                    
                y_head = int(col["y"])
                dist = y_head - y
                
                if 0 <= dist < col["length"]:
                    char = chars[y * width + x]
                    if dist == 0:
                        full_text.append(char, style="bold #ffffff")
                    elif dist < 3:
                        full_text.append(char, style="bold #00ff00")
                    elif dist < col["length"] // 2:
                        full_text.append(char, style="#008800")
                    else:
                        full_text.append(char, style="#004400")
                else:
                    full_text.append(" ")
            if y < height - 1:
                full_text.append("\n")
        
        return full_text

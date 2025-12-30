"""
GEMMIS UI CSS
"""

PRIMARY_COLOR = "#f97ff5" # Synthwave Pink as default base for CSS variables if not overridden
BACKGROUND_COLOR = "#0a0a0a"

STATIC_CSS = """
Screen {
    background: $bg-dark;
    color: $text-primary;
    layers: base matrix overlay;
}

#matrix-rain {
    display: none;
    width: 100%;
    height: 100%;
    layer: matrix;
    background: transparent;
}

#glitch-overlay {
    display: none;
    width: 100%;
    height: 100%;
    layer: matrix; /* Reuse matrix layer or add a new one */
    background: transparent;
}

/* Sidebar Layout */
Sidebar {
    width: 32;
    dock: left;
    background: $bg-dark;
    border-right: heavy $primary;
    scrollbar-size: 0 0;
    transition: border 500ms;
}

Sidebar.pulse {
    border-right: heavy $secondary;
}

/* Avatar Container */
AvatarWidget {
    height: 14;
    width: 100%;
    padding: 0;
    margin-bottom: 1;
    border-bottom: solid $secondary;
}

/* Sidebar Widgets */
SystemStats, OllamaModels, SessionList {
    padding: 1;
    border-bottom: solid $dim;
    height: auto;
    background: $bg-dark;
}
""" + """
ListView {
    height: auto;
    max-height: 10;
}

/* Chat Area */
#main-area {
    padding: 0 1;
}

#chat-display {
    height: 1fr;
    overflow-y: scroll;
    scrollbar-gutter: stable;
}

/* Chat Bubbles - Circuit Style */
ChatBubble {
    background: $bg-light;
    border: heavy $primary; /* Closest we can get to circuit board in CSS */
    padding: 1 2;
    margin: 1 0;
    width: 100%;
    max-width: 95%;
}

ChatBubble.user {
    border: heavy $secondary;
    margin-left: 10;
    text-align: right;
}

ChatBubble.assistant {
    border: heavy $primary;
    margin-right: 10;
}

ChatBubble.system {
    border: dashed $dim;
    color: $dim;
    text-align: center;
    background: $bg-dark;
}

/* Code Blocks */
CodeBlock {
    background: #1a1a1a;
    border-left: solid $accent;
    padding: 1;
    margin: 1 0;
}

CodeBlock Markdown {
    width: 100%;
}

/* ASCII Art specific styling */
CodeBlock.ascii {
    padding: 0;
    border: none;
    background: transparent;
}

CodeBlock.ascii Markdown {
    color: #00ff00; /* Matrix Green for ASCII */
    text-style: bold;
}

.code-toolbar {
    height: 1;
    background: $dim;
    color: $bg-dark;
    align: right middle;
}

/* Input Area */
#message-input {
    dock: bottom;
    height: 3;
    border: heavy $accent;
    background: $bg-dark;
    color: $text-primary;
}

#message-input:focus {
    border: heavy $primary;
}

/* Tabs */
Tabs {
    dock: top;
}

Tab {
    color: $dim;
}

Tab.-active {
    color: $primary;
    text-style: bold;
    border-bottom: heavy $primary;
}
"""

def get_css() -> str:
    from .theme import get_current_theme
    from textwrap import dedent
    
    theme = get_current_theme()

    # We strip the "bold " part if present for CSS hex codes
    def clean_color(c):
        return c.replace("bold ", "")

    variables = dedent(f"""
    $primary: {clean_color(theme.primary)};
    $secondary: {clean_color(theme.secondary)};
    $accent: {clean_color(theme.accent)};
    $warning: {clean_color(theme.warning)};
    $error: {clean_color(theme.error)};
    $success: {clean_color(theme.success)};
    $dim: {clean_color(theme.dim)};
    $bg-dark: {clean_color(theme.bg_dark)};
    $bg-light: {clean_color(theme.bg_light)};
    $text-primary: {clean_color(theme.text_primary)};
    $text-secondary: {clean_color(theme.text_secondary)};
    """).strip()

    # OMEGA UPGRADE: CRT SCANLINES & GLOW
    extra_css = """
    /* --- OMEGA VISUAL UPGRADES --- */

    /* CRT Scanline Simulation */
    Screen {
        scrollbar-background: $bg-dark;
        scrollbar-color: $primary;
    }

    /* Glowing Text Effect for Headers */
    Label, .bold {
        text-style: bold;
        color: $primary;
    }

    /* The Avatar needs to look mostly alive */
    AvatarWidget {
        border-bottom: heavy $accent;
    }

    /* Cyberpunk Input Field */
    #message-input {
        background: $bg-dark;
        border: heavy $secondary;
        color: $text-primary;
        text-style: bold;
        transition: border 500ms;
    }
    
    #message-input.pulse {
        border: heavy $accent;
    }
    
    #message-input:focus {
        border: heavy $primary;
        background: #1a1a1a;
        tint: $primary 10%;
    }

    /* Scrollbar Styling */
    VerticalScroll > .scrollbar {
        background: $bg-dark;
        color: $dim;
    }
    
    VerticalScroll > .scrollbar:hover {
        color: $primary;
    }

    /* --- DASHBOARD v3.0 --- */
    #dashboard-grid {
        layout: grid;
        grid-size: 1 2;
        grid-rows: 14 1fr; /* Fixed height for gauges */
        padding: 1;
    }

    #gauges-row {
        height: 14;
        width: 100%;
        margin-bottom: 1;
    }

    SystemGauge {
        width: 1fr;
        height: 100%;
        margin: 0 1;
        border: heavy $dim;
        background: $bg-dark;
        padding: 1;
    }
    
    SystemGauge:hover {
        border: heavy $primary;
    }

    .gauge-header {
        height: 1;
        align: center middle;
        margin-bottom: 1;
    }

    .gauge-label {
        color: $secondary;
        text-style: bold;
    }

    .gauge-value {
        color: $primary;
        text-style: bold;
    }

    ProgressBar {
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    
    /* Gauge Colors */
    .gauge-cyan > .bar--bar { color: $primary; background: $primary 30%; }
    .gauge-magenta > .bar--bar { color: $accent; background: $accent 30%; }
    .gauge-yellow > .bar--bar { color: $warning; background: $warning 30%; }

    Sparkline {
        width: 100%;
        height: 5;
        color: $success;
    }
    
    #process-container {
        border-top: solid $dim;
        padding-top: 1;
    }
    
    .section-header {
        text-style: bold underline;
        color: $dim;
        margin-bottom: 1;
    }

    /* NEON PULSE ANIMATION */
    #message-input:focus {
        border: heavy $primary;
        background: #1a1a1a;
        tint: $primary 10%; 
        /* Pulse not fully supported in TUI CSS yet without keyframes, using tint instead */
    }
    
    /* Custom Scrollbar for Table */
    DataTable {
        background: $bg-dark;
        scrollbar-gutter: stable;
    }
    
    DataTable > .datatable--cursor {
        background: $primary;
        color: $bg-dark;
        text-style: bold;
    }

    /* --- HUD --- */
    .hud {
        dock: top;
        height: 1;
        width: 100%;
        background: $bg-dark;
        color: $dim;
        content-align: center middle;
        text-style: bold;
        layer: overlay;
    }

    #hud-bottom {
        dock: bottom;
    }

    /* --- LIVING BORDERS --- */
    .phase-1 { border: heavy $primary; }
    .phase-2 { border: heavy $secondary; }
    .phase-3 { border: heavy $accent; }

    /* --- DATA BLOCKS --- */
    ProcessCard {
        height: auto;
        min-height: 4;
        width: 100%;
        margin: 0 0 1 0;
        padding: 0 1;
        border: solid $dim;
        background: $bg-dark;
    }

    ProcessCard:hover {
        border: solid $primary;
    }

    ProcessCard.surge {
        border: solid $warning;
    }

    .process-header {
        width: 100%;
        color: $text-primary;
        text-style: bold;
        padding-bottom: 0;
    }

    .process-row {
        width: 100%;
        height: 1;
    }
    """

    return variables + STATIC_CSS + extra_css
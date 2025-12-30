"""
<<<<<<< HEAD
GEMMIS UI CSS Generation
Generates Textual CSS dynamically based on the active theme
"""

from .theme import get_current_theme

def get_css() -> str:
    """Generate CSS for the Textual App based on current theme"""
    theme = get_current_theme()

    return f"""
    Screen {{
        background: {theme.BG_DARK};
        color: {theme.TEXT_PRIMARY};
    }}

    /* --- SIDEBAR --- */
    Sidebar {{
        width: 35;
        dock: left;
        background: {theme.BG_DARK};
        border-right: heavy {theme.BORDER_PRIMARY};
        height: 100%;
    }}

    SystemMonitorWidget {{
        height: auto;
        padding: 1;
        margin-bottom: 1;
        border-bottom: heavy {theme.BORDER_SECONDARY};
    }}

    SessionListWidget {{
        height: 1fr;
        padding: 1;
    }}

    /* --- TABS --- */
    TabbedContent {{
        height: 1fr;
    }}

    TabPane {{
        padding: 0;
    }}

    Tabs {{
        background: {theme.BG_LIGHT};
        color: {theme.DIM};
        dock: top;
    }}

    Tab {{
        padding: 1 2;
    }}

    Tab.-active {{
        background: {theme.BG_DARK};
        color: {theme.ACCENT};
        text-style: bold;
        border-top: heavy {theme.PRIMARY};
    }}

    /* --- CHAT INTERFACE --- */
    #chat-container {{
        height: 1fr;
        padding: 1;
        scrollbar-gutter: stable;
        overflow-y: scroll;
    }}

    ChatBubble {{
        width: 100%;
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
        background: {theme.BG_LIGHT};
        border: heavy {theme.BORDER_SECONDARY};
    }}

    ChatBubble.user {{
        border: heavy {theme.PRIMARY};
        background: {theme.BG_LIGHT};
        margin-left: 4;
    }}

    ChatBubble.assistant {{
        border: heavy {theme.SECONDARY};
        background: {theme.BG_DARK};
        margin-right: 4;
    }}

    ChatBubble.tool {{
        border: dashed {theme.WARNING};
        background: {theme.BG_DARK};
    }}

    CodeBlock {{
        background: {theme.BG_DARK};
        border: solid {theme.DIM};
        margin: 1 0;
        height: auto;
    }}

    CodeBlock > Static {{
        padding: 1;
    }}

    CodeBlock > Horizontal {{
        height: auto;
        background: {theme.BG_LIGHT};
        dock: top;
        padding: 0 1;
    }}

    CodeBlock Button {{
        min-width: 8;
        height: 1;
        margin-right: 1;
        background: {theme.PRIMARY};
        color: {theme.BG_DARK};
        border: none;
    }}

    CodeBlock Button:hover {{
        background: {theme.ACCENT};
    }}

    /* --- INPUT AREA --- */
    Input {{
        dock: bottom;
        width: 100%;
        height: 3;
        border: heavy {theme.BORDER_PRIMARY};
        background: {theme.BG_DARK};
        color: {theme.TEXT_PRIMARY};
        padding: 0 1;
    }}

    Input:focus {{
        border: heavy {theme.ACCENT};
    }}

    /* --- MODALS --- */
    KillProcessModal {{
        align: center middle;
    }}

    #kill-dialog {{
        padding: 2;
        width: 60;
        height: auto;
        border: heavy {theme.ERROR};
        background: {theme.BG_DARK};
    }}

    ToolConfirmationModal {{
        align: center middle;
    }}

    #tool-dialog {{
        padding: 2;
        width: 70;
        height: auto;
        border: heavy {theme.WARNING};
        background: {theme.BG_DARK};
    }}

    DataTable {{
        background: {theme.BG_DARK};
        color: {theme.TEXT_PRIMARY};
        border: solid {theme.DIM};
    }}

    DataTable > .datatable--header {{
        background: {theme.BG_LIGHT};
        color: {theme.ACCENT};
        text-style: bold;
    }}

    DataTable > .datatable--cursor {{
        background: {theme.PRIMARY};
        color: {theme.BG_DARK};
    }}

    Sparkline {{
        height: 3;
        width: 100%;
        color: {theme.PRIMARY};
    }}

    .ram-spark {{
        color: {theme.SECONDARY};
    }}
    """
=======
GEMMIS UI CSS
"""

PRIMARY_COLOR = "#00ff00"
BACKGROUND_COLOR = "#0a0a0a"

STATIC_CSS = f"""
Screen {{
    background: {BACKGROUND_COLOR};
    color: {PRIMARY_COLOR};
}}

Sidebar {{
    width: 30;
    dock: left;
    background: {BACKGROUND_COLOR};
    border-right: heavy {PRIMARY_COLOR};
}}

SystemStats, OllamaModels, SessionList {{
    padding: 1;
    border-bottom: heavy {PRIMARY_COLOR};
    height: auto;
}}

#process-table {{
    height: 1fr;
}}

#log-viewer {{
    height: 1fr;
    border: solid {PRIMARY_COLOR};
    padding: 1;
}}

#chat-display {{
    height: 1fr;
    overflow-y: scroll;
    scrollbar-gutter: stable;
}}

#message-input {{
    dock: bottom;
    height: 3;
}}
"""

def get_css() -> str:
    return STATIC_CSS
>>>>>>> origin/main

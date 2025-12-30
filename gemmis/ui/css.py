"""
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

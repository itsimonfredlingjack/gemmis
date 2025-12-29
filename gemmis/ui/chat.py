"""
GEMMIS Chat UI - Message rendering with theme support and syntax highlighting
"""

import re
import time

from rich import box
from rich.align import Align
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from .theme import get_current_theme
from .effects import GhostTyper
from .boxes import TECH_BOX, CYBER_BOX


def render_content_with_code(content: str) -> Group:
    """Render content with syntax highlighting for code blocks.

    Parses markdown-style code blocks and renders them with syntax highlighting.
    """
    Colors = get_current_theme()

    # Pattern to match code blocks: ```language\ncode\n```
    code_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)

    parts = []
    last_end = 0

    for match in code_pattern.finditer(content):
        # Add text before code block
        if match.start() > last_end:
            text_before = content[last_end : match.start()]
            if text_before.strip():
                parts.append(Markdown(text_before))

        # Extract language and code
        language = match.group(1) or "text"
        code = match.group(2).rstrip()

        # Create syntax-highlighted code block
        try:
            syntax = Syntax(
                code,
                language,
                theme=Colors.code_theme,
                line_numbers=False,
                word_wrap=True,
                background_color=Colors.BG_DARK,
            )
            parts.append(syntax)
        except Exception:
            # Fallback to plain text if syntax highlighting fails
            parts.append(Text(f"```{language}\n{code}\n```", style=Colors.TEXT_SECONDARY))

        last_end = match.end()

    # Add remaining text after last code block
    if last_end < len(content):
        remaining = content[last_end:]
        if remaining.strip():
            parts.append(Markdown(remaining))

    # If no code blocks found, return rendered Markdown
    if not parts:
        return Group(Markdown(content))

    return Group(*parts)


def render_message(role: str, content: str, width: int = None) -> Panel:
    """Render a single chat message with theme-aware styling and syntax highlighting."""
    Colors = get_current_theme()

    # Handle Tool Results
    if role == "tool":
        return Panel(
            Text(f"{content}", style=Colors.DIM),
            title=f"[{Colors.DIM}] TOOL_OUTPUT [/]",
            title_align="left",
            border_style=Colors.DIM,
            style=f"on {Colors.BG_DARK}",
            box=box.ROUNDED,
            padding=(0, 2),
            width=width,
        )

    # Check if content has code blocks
    if "```" in content and role == "assistant":
        # Use syntax highlighting for code blocks
        message_content = render_content_with_code(content)
    else:
        # Use Markdown rendering for all messages to support tables/formatting
        message_content = Markdown(content)

    # Get model name for assistant messages (import dynamically to get latest value)
    from ..config import MODEL_NAME as _MODEL_NAME
    model_display = _MODEL_NAME.split(":")[0].upper()

    if role == "user":
        # User message - right aligned
        # For user input, we use simpler text rendering to avoid Markdown messing up raw input
        return Panel(
            Text(content, style=Colors.TEXT_PRIMARY),
            title=f"[{Colors.SECONDARY}] USER_INPUT [/]",
            title_align="right",
            border_style=Colors.BORDER_SECONDARY,
            style=f"on {Colors.BG_LIGHT}",
            box=box.ROUNDED,
            padding=(1, 2),
            width=width,
        )
    else:
        # Assistant message - left aligned
        return Panel(
            message_content,
            title=f"[{Colors.PRIMARY}] {model_display}_CORE [/]",
            title_align="left",
            border_style=Colors.BORDER_PRIMARY,
            style=f"on {Colors.BG_LIGHT}",
            box=TECH_BOX, # Cyber look
            padding=(1, 2),
            width=width,
        )


def render_chat(messages: list[dict], max_visible: int = 6) -> Panel:
    """Render chat history panel with theme-aware styling."""
    Colors = get_current_theme()
    visible = messages[-max_visible:] if messages else []

    if not visible:
        welcome_text = Text()
        welcome_text.append("INITIALIZING LINK...\n", style=Colors.DIM)
        from ..config import MODEL_NAME as _MODEL_NAME
        model_display = _MODEL_NAME.split(":")[0].upper()
        welcome_text.append(f"CONNECTED TO {model_display} NET", style=f"bold {Colors.PRIMARY}")
        welcome_text.append("\n\n", style=Colors.DIM)
        welcome_text.append("AWAITING INPUT >_", style=f"blink {Colors.SECONDARY}")
        content = Align.center(welcome_text, vertical="middle")
    else:
        panels = [render_message(m["role"], m["content"]) for m in visible]
        content = Align(Group(*panels), vertical="bottom")

    return Panel(
        content,
        title=f"[{Colors.PRIMARY}] COMMLINK [/]",
        border_style=Colors.BORDER_PRIMARY,
        style=f"on {Colors.BG_DARK}",
        box=TECH_BOX, # Main container
        padding=(1, 1),
    )


def render_chat_streaming(
    messages: list[dict],
    current_response: str,
    state: str,
    max_visible: int = 1000,
    console_width: int = None,
    console_height: int = None,
    effects: dict = None,
) -> Panel:
    """Render chat with streaming response - always shows latest messages (autoscroll)."""
    Colors = get_current_theme()
    effects = effects if effects is not None else {}

    all_messages = list(messages)
    panels_to_render = []

    # Get model display name (import dynamically to get latest value)
    from ..config import MODEL_NAME as _MODEL_NAME
    model_display = _MODEL_NAME.split(":")[0].upper()

    # Determine widths and heights
    msg_width = int(console_width * 0.85) if console_width else None

    # Calculate max lines based on console height
    max_lines = max(10, console_height - 8) if console_height else 15

    # Create the "Current Response" panel if needed
    current_panel = None
    if current_response or state in ("thinking", "speaking", "generating"):
        if state == "thinking":
            title = f"[{Colors.WARNING}] ANALYZING DATA STREAM... [/]"
            border_color = Colors.WARNING
            box_style = box.ROUNDED
        else:
            title = f"[{Colors.PRIMARY}] {model_display}_TRANSMISSION [/]"
            border_color = Colors.BORDER_PRIMARY
            box_style = box.HEAVY

        # Special handling for Tool Execution logs (detected by content)
        if current_response.startswith("🔧 EXEC_TOOL:") or current_response.startswith("✅ COMPLETE:") or current_response.startswith("❌ ERROR:"):
             display_content = Text(current_response, style=Colors.DIM)
             title = f"[{Colors.ACCENT}] SYSTEM_ACTION [/]"
             box_style = box.DOUBLE
        elif not current_response:
            # Typing animation
            display_text = Text()
            display_text.append("█", style=f"blink {Colors.PRIMARY}")
            display_content = display_text
        else:
            # Manual Autoscroll / Text Truncation
            lines = current_response.splitlines()
            if len(lines) > max_lines:
                visible_lines = lines[-max_lines:]
                # We can't safely use Markdown on truncated text usually, but let's try
                # to keep it simple for streaming: Text with cursor
                # Use GhostTyper if available
                display_content = Text("\n".join(visible_lines), style=Colors.TEXT_PRIMARY)
            else:
                # If short enough, render with markdown/code support
                if "```" in current_response:
                    display_content = render_content_with_code(current_response)
                else:
                    # GHOST TYPER LOGIC
                    if state in ("generating", "speaking"):
                        if "ghost_typer" not in effects:
                            effects["ghost_typer"] = GhostTyper(current_response)
                        else:
                            effects["ghost_typer"].update(current_response)
                        
                        display_content = effects["ghost_typer"].render()
                    else:
                        display_content = Text(current_response, style=Colors.TEXT_PRIMARY)

        # Add blinking cursor if it's a Text object and we are generating
        # (GhostTyper returns Text, so this still works)
        if isinstance(display_content, Text) and state in ("generating", "speaking"):
             if int(time.time() * 2) % 2 == 0:
                display_content.append(" █", style=f"blink {Colors.PRIMARY}")

        current_panel = Panel(
            display_content,
            title=title,
            title_align="left",
            border_style=border_color,
            style=f"on {Colors.BG_LIGHT}",
            box=TECH_BOX, # Use Tech Box for streaming panel
            padding=(1, 2),
            width=msg_width,
        )

    # Dynamic history limit based on available height
    if console_height:
        avg_msg_height = 6
        available_lines = console_height - (max_lines if current_panel else 0) - 4
        calculated_limit = max(1, available_lines // avg_msg_height)

        if current_panel:
            history_limit = max(1, calculated_limit - 1)
        else:
            history_limit = calculated_limit

        history_limit = min(history_limit, 10)
    else:
        history_limit = 2 if current_panel else 3

    visible_history = (
        all_messages[-history_limit:] if len(all_messages) > history_limit else all_messages
    )

    for m in visible_history:
        panels_to_render.append(render_message(m["role"], m["content"], width=msg_width))

    if current_panel:
        panels_to_render.append(current_panel)

    if not panels_to_render:
        welcome_text = Text()
        welcome_text.append("INITIALIZING SECURE CONNECTION...\n", style=Colors.DIM)
        welcome_text.append(f"ACCESS GRANTED: {model_display}", style=f"bold {Colors.PRIMARY}")
        welcome_text.append("\n\n", style=Colors.DIM)
        welcome_text.append("AWAITING INPUT >_", style=f"blink {Colors.SECONDARY}")
        content = Align.center(welcome_text, vertical="middle")
    else:
        content = Align(Group(*panels_to_render), vertical="bottom")

    title_styles = {
        "thinking": (f"[{Colors.WARNING}] SYSTEM BUSY [/]", Colors.WARNING),
        "speaking": (f"[{Colors.SECONDARY}] INCOMING DATA [/]", Colors.SECONDARY),
        "idle": (f"[{Colors.PRIMARY}] SECURE CHAT [/]", Colors.PRIMARY),
    }
    title, border_color = title_styles.get(
        state, (f"[{Colors.PRIMARY}] SECURE CHAT [/]", Colors.PRIMARY)
    )

    return Panel(
        content,
        title="[bold green]NEURAL_UPLINK[/]",
        border_style="bright_cyan",
        style=f"on {Colors.BG_DARK}",
        box=CYBER_BOX,
        padding=(1, 2),
        expand=True,
    )

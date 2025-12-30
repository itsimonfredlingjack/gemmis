"""
GEMMIS CLI - Neural Interface Terminal
Main Application
"""

import asyncio
import json
import traceback
import random
import time

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from .ui.boxes import CIRCUIT_BOX, CYBER_BOX, SCAN_BOX

# Optional: TextBlob for sentiment analysis (graceful degradation)
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

from .commands import handle_command
from .config import MODEL_NAME, save_default_config
from .ollama_client import OllamaClient, OllamaError
from .state import AppState
from .system_monitor import get_monitor
from .tools import execute_tool_call, is_sensitive
from .ui.boot import run_boot_sequence
from .audio import get_audio
from .ui.effects import HexDump
from .ui.theme import set_theme, get_current_theme
from .ui.input import get_random_hint


def create_layout(console: Console = None) -> Layout:
    """Create the initial UI layout structure"""
    layout = Layout()

    # Main structure: Header, Body, Footer
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3)
    )
    
    # Split body into chat and stats
    layout["body"].split_row(
        Layout(name="chat", ratio=8),  # Much larger chat area (80%)
        Layout(name="stats", ratio=2),  # Stats panel (20%)
    )
    return layout


def update_layout(
    layout: Layout,
    state: AppState,
    console: Console = None,
    render_chat_streaming=None,
    render_stats_panel=None,
) -> Layout:
    """Update the content of the existing layout"""
    # Get console dimensions for proper text wrapping and height calculation
    console_width = None
    console_height = None
    
    # Import render_header locally to avoid circular imports
    from .ui.panels import render_header
    
    if console:
        try:
            console_width = console.width
            # Reserve space for header (3) + footer (3) + prompt buffer
            # User requested console.height - 2 to "fool" layout for prompt positioning
            console_height = console.height - 2
        except Exception:
            pass

    # Header
    layout["header"].update(render_header(state.connected, state.avatar_state))

    # Chat
    if render_chat_streaming:
        layout["chat"].update(
            render_chat_streaming(
                state.messages,
                state.current_response,
                state.avatar_state,
                console_width=console_width,
                console_height=console_height,
                effects=state.effects,
            )
        )

    # Stats
    if render_stats_panel:
        layout["stats"].update(
            render_stats_panel(
                state.connected,
                state.tokens,
                state.tokens_per_sec,
                state.status,
                state.system_stats,
                state.avatar_state,
                cpu_history=state.cpu_history,
                mem_history=state.mem_history,
                tps_history=state.tokens_per_sec_history,
                effects_state=state.effects,
            )
        )
    
    # Footer - render a placeholder or border to frame the input
    from .ui.theme import get_current_theme
    Colors = get_current_theme()
    
    # Footer panel with lighter background to make prompt visible
    # The prompt_toolkit prompt will be displayed in this area
    # NOTE: In the new input loop, prompt_toolkit renders ON TOP of this.
    # We just provide a frame.
    footer_text = Text("", style=Colors.TEXT_PRIMARY)
    layout["footer"].update(
        Panel(
            footer_text,
            border_style=Colors.BORDER_PRIMARY,
            style=f"on {Colors.BG_LIGHT}",  # Lighter background for better visibility
            box=CYBER_BOX,
            padding=(0, 1),
        )
    )

    return layout


async def async_main(
    model: str | None = None,
    theme: str = "synthwave",
    persona: str = "default",
    minimal: bool = False,
    debug: bool = False,
    no_screen: bool = False,
) -> None:
    """Main application loop (Async)

    Args:
        model: Ollama model to use (overrides config)
        theme: Visual theme name
        persona: AI persona name
        minimal: Skip boot animation
        debug: Enable debug logging
        no_screen: Disable alternate screen buffer mode (for terminal compatibility)
    """
    # Initialize config
    save_default_config()

    # Update MODEL_NAME in config if model is provided as argument
    if model:
        from . import config
        config.MODEL_NAME = model

    # Set theme before importing UI components
    from .ui import theme as theme_module

    theme_module.set_theme(theme)

    # Now import UI components (they will use the set theme)
    from .ui.chat import render_chat_streaming
    from .ui.panels import render_stats_panel

    # Get Colors after theme is set
    Colors = theme_module.get_current_theme()

    # Console with proper terminal configuration to avoid ANSI escape code issues
    import sys
    import os
    
    # Detect terminal capabilities
    is_tty = sys.stdout.isatty()
    use_screen_mode = not no_screen and is_tty
    
    # Get terminal encoding (default to UTF-8)
    encoding = sys.stdout.encoding or "utf-8"
    
    # Check if terminal supports colors (from environment or detection)
    # Some terminals need explicit force_terminal, others don't
    force_terminal = None
    if is_tty:
        # Only force terminal mode if we're actually in a terminal
        # and the terminal supports it (not a dumb terminal)
        term = os.environ.get("TERM", "")
        colorterm = os.environ.get("COLORTERM", "")
        
        # Check if terminal supports ANSI escape codes
        # Most modern terminals (including Kitty) support this
        if term and term.lower() != "dumb":
            force_terminal = True
        # If COLORTERM is set, terminal definitely supports colors
        elif colorterm:
            force_terminal = True
    
    # Create console with explicit encoding and proper terminal detection
    # The key is to ensure Rich writes directly to stdout without buffering
    console = Console(
        force_terminal=force_terminal,
        file=sys.stdout,
        width=None,  # Auto-detect
        height=None,  # Auto-detect
        legacy_windows=False,  # Modern Windows terminals support ANSI
        # Don't use legacy_windows mode even on Windows - modern terminals support ANSI
    )

    # Create a helper to update layout with the right renderers
    def do_update_layout(layout: Layout, state: AppState, cons: Console = None) -> Layout:
        return update_layout(
            layout,
            state,
            cons,
            render_chat_streaming=render_chat_streaming,
            render_stats_panel=render_stats_panel,
        )

    # Run boot sequence (unless --minimal)
    if not minimal:
        run_boot_sequence(console, theme=theme)
    
    # Audio Init & Startup Sound
    audio = get_audio()
    if audio.enabled:
        audio.play("startup")

    # Create state with persona
    state = AppState()

    # Set persona system prompt
    if persona != "default":
        from .personas import get_persona_prompt

        state.system_prompt = get_persona_prompt(persona)

    # Create client with optional model override (needed early for memory initialization)
    effective_model = model if model else MODEL_NAME
    client = OllamaClient(model=effective_model)

    # Initialize memory system (optional, graceful degradation if fails)
    store = None
    try:
        from .memory import Store, SessionManager
        from pathlib import Path

        # Use GEMMIS config directory for storage
        gemmis_config_dir = Path.home() / ".config" / "gemmis-cli"
        db_path = gemmis_config_dir / "memory.db"
        gemmis_config_dir.mkdir(parents=True, exist_ok=True)

        store = Store(str(db_path))
        await store.connect()

        # Try to initialize vector store (optional, requires chromadb)
        vector_store = None
        try:
            from .memory import VectorStore, CHROMADB_AVAILABLE
            if CHROMADB_AVAILABLE:
                vector_store = VectorStore()
                await vector_store.initialize()
        except Exception:
            pass  # Vector store is optional

        session_manager = SessionManager(store, vector_store)
        session_id = await session_manager.create_session(f"GEMMIS Session - {effective_model}")

        state.session_manager = session_manager
        state.current_session_id = session_id
        state.use_memory = True

        # Load existing messages from session
        context = await session_manager.get_context()
        state.messages = [
            {"role": msg.role, "content": msg.content}
            for msg in context
            if msg.role != "system"
        ]
    except Exception as e:
        # Graceful degradation - continue without memory
        state.use_memory = False
        if debug:
            console.print(f"[{Colors.DIM}]Memory system unavailable: {e}[/]")

    # Welcome - Cyberpunk Style
    console.clear()
    
    # Initialize system monitor
    monitor = get_monitor()

    # Create persistent layout
    layout = create_layout(console)

    # Define tool executor context
    live_context = None

    # Create prompt session for async input (needed by safe_tool_executor too)
    session = PromptSession()

    # --- FIXED TOOL EXECUTOR ---
    async def safe_tool_executor(tool_call, tool_name, tool_args):
        """
        Executes tools with a safety check using the correct 'session' variable.
        """
        # 1. Clean color codes for the prompt (HTML style doesn't like 'bold')
        warning_col = Colors.WARNING.replace("bold ", "").strip()

        # 2. Construct the HTML prompt
        # WE MUST USE 'session', NOT 'prompt_session'
        prompt_html = HTML(
            f"<style fg='{warning_col}'>⚠ ALLOW EXECUTION of </style>"
            f"<b>{tool_name}</b>"
            f"<style fg='{warning_col}'>? [y/N]: </style>"
        )

        try:
            # 3. The Critical Fix: Use 'session' (defined in async_main scope)
            # patch_stdout handles ensuring this prints above the prompt line correctly
            response = await session.prompt_async(prompt_html)

            if response.strip().lower() == 'y':
                return True

            console.print(f"[{Colors.ERROR}]User denied permission.[/{Colors.ERROR}]")
            return False

        except (EOFError, KeyboardInterrupt):
            return False
    # ---------------------------

    # ENTER FULLSCREEN TUI MODE
    # patch_stdout() prevents prompt_toolkit from breaking Rich's screen buffer
    # screen=True locks the terminal in alternate screen mode (like vim/htop)
    # Use use_screen_mode to allow fallback for terminals with compatibility issues
    if debug:
        console.print(f"[dim]Screen mode: {use_screen_mode}, TTY: {is_tty}, Encoding: {encoding}[/]")
    
    # Ensure stdout is in the right state before entering Live context
    sys.stdout.flush()
    sys.stderr.flush()
    
    try:
        # Use patch_stdout() to manage stdout/stderr while allowing PromptSession to work
        # This is key for the "blind typing" fix - it ensures input line is always visible
        with patch_stdout():
            # screen=True = Fullscreen (no scrollback history on screen)
            # refresh_per_second=10 = Faster UI updates
            # redirect_stderr=False = Let patch_stdout handle stderr if needed
            with Live(
                layout,
                console=console,
                screen=use_screen_mode,
                refresh_per_second=10,
                redirect_stderr=False
            ) as live:

                live_context = live
                live.refresh()

                # Main Application Loop
                while True:
                    # --- UPDATE DATA ---
                    # Update system stats (runs once per loop iteration)
                    cpu_stats = monitor.get_cpu_stats()
                    mem_stats = monitor.get_memory_stats()

                    state.system_stats = {
                        "cpu": cpu_stats,
                        "memory": mem_stats,
                        "disk": monitor.get_disk_stats(),
                    }

                    # Update history for sparklines
                    if cpu_stats:
                        state.cpu_history.append(cpu_stats.get("usage", 0))
                        if len(state.cpu_history) > 20:
                            state.cpu_history.pop(0)

                    if mem_stats:
                        state.mem_history.append(mem_stats.get("percent", 0))
                        if len(state.mem_history) > 20:
                            state.mem_history.pop(0)

                    # Update TPS history
                    if state.status != "GENERATING":
                        state.tokens_per_sec_history.append(0.0)
                    else:
                        state.tokens_per_sec_history.append(state.tokens_per_sec)
                    if len(state.tokens_per_sec_history) > 20:
                        state.tokens_per_sec_history.pop(0)

                    # --- UPDATE UI ---
                    update_layout(
                        layout,
                        state,
                        console,
                        render_chat_streaming=render_chat_streaming,
                        render_stats_panel=render_stats_panel
                    )

                    # --- INPUT FIX (Here is the magic) ---
                    try:
                        # Define a style that GUARANTEES visibility (Neon Green/White)
                        # This overwrites any dark theme colors that might hide input
                        prompt_style = Style.from_dict({
                            'prompt': '#00ff00 bold',       # "COMMAND"
                            'input': '#ffffff',             # Input text (White)
                        })

                        # Prompt HTML - Clean and clear
                        prompt_html = HTML(
                            "<prompt>COMMAND_OVERRIDE</prompt> <style fg='#444444'>></style> "
                        )

                        # Get a random hint
                        hint_text = get_random_hint()
                        hint_html = HTML(f"<style fg='{Colors.dim}'>  ({hint_text})</style>")

                        # patch_stdout ensures this line "floats" above/below graphics correctly
                        user_input = await session.prompt_async(
                            prompt_html,
                            style=prompt_style,
                            rprompt=hint_html
                        )
                        
                        user_input = user_input.strip()

                        if not user_input:
                            continue

                        # SENTIMENT ANALYSIS & THEME INJECTION
                        if TEXTBLOB_AVAILABLE and not user_input.startswith("/"):
                            try:
                                blob = TextBlob(user_input)
                                sentiment = blob.sentiment.polarity
                                current_theme_name = get_current_theme().name.lower()

                                if sentiment < -0.5 and current_theme_name != "cyberpunk":
                                    set_theme("cyberpunk")
                                    Colors = get_current_theme()
                                elif sentiment > 0.5 and current_theme_name != "nord":
                                    set_theme("nord")
                                    Colors = get_current_theme()
                            except Exception:
                                pass

                        # Handle commands
                        if user_input.startswith("/"):
                            parts = user_input.split(maxsplit=1)
                            cmd = parts[0].lower()
                            arg = parts[1] if len(parts) > 1 else None

                            should_continue = await handle_command(cmd, arg, state, console, client, monitor)
                            if not should_continue:
                                break
                            continue

                        # Add user message
                        await state.add_message("user", user_input)
                        state.avatar_state = "thinking"
                        state.status = "THINKING"
                        state.tokens = 0
                        state.current_response = ""

                        # Update UI to show "Thinking"
                        update_layout(layout, state, console, render_chat_streaming, render_stats_panel)
                        # No manual refresh needed with refresh_per_second=10, but doesn't hurt

                        # Start streaming animation
                        state.avatar_state = "speaking"
                        state.status = "GENERATING"

                        # Streaming Loop
                        tools_enabled = True
                        max_tool_iterations = 5
                        tool_iterations = 0

                        while tool_iterations < max_tool_iterations:
                            tool_called = False

                            try:
                                # Pass safe_tool_executor
                                async for token, stats, tool_info in client.chat_stream(
                                    await state.get_chat_messages(),
                                    tools_enabled=tools_enabled,
                                    tool_executor=safe_tool_executor,
                                ):
                                    if tool_info and tool_info.get("type") == "tool_call":
                                        tool_called = True
                                        tool_name = tool_info.get("tool_name", "")
                                        tool_args = tool_info.get("arguments", {})
                                        tool_result = tool_info.get("result", {})

                                        args_str = ", ".join(f"{k}={v}" for k, v in tool_args.items() if v)
                                        tool_msg = f"🔧 EXEC_TOOL: {tool_name}({args_str})" if args_str else f"🔧 EXEC_TOOL: {tool_name}()"

                                        state.current_response = tool_msg

                                        if tool_name == "read_file":
                                            state.effects["hexdump"] = HexDump()

                                        update_layout(layout, state, console, render_chat_streaming, render_stats_panel)
                                        # live.refresh() # handled by refresh_per_second
                                        await asyncio.sleep(0.5)

                                        state.messages.append({
                                            "role": "assistant",
                                            "content": None,
                                            "tool_calls": [{"type": "function", "function": {"name": tool_name, "arguments": json.dumps(tool_args) if tool_args else "{}"}}]
                                        })

                                        state.messages.append({
                                            "role": "tool",
                                            "name": tool_name,
                                            "content": json.dumps(tool_result, ensure_ascii=False),
                                        })

                                        if "error" in tool_result:
                                            result_msg = f"❌ ERROR: {tool_result.get('error')}"
                                        else:
                                            result_msg = f"✅ COMPLETE: {tool_name}"
                                        state.current_response = result_msg

                                        if "hexdump" in state.effects:
                                            del state.effects["hexdump"]

                                        update_layout(layout, state, console, render_chat_streaming, render_stats_panel)
                                        await asyncio.sleep(0.3)

                                        state.current_response = ""
                                        break

                                    if token:
                                        state.current_response += token
                                        # Audio throttle
                                        if random.random() < 0.3:
                                            audio.play("token")

                                        update_layout(layout, state, console, render_chat_streaming, render_stats_panel)
                                        # Live updates automatically

                                    if stats:
                                        state.tokens = stats.tokens_generated
                                        state.tokens_per_sec = stats.tokens_per_second
                            except Exception as e:
                                audio.play("error")
                                if tools_enabled and tool_iterations == 0:
                                    tools_enabled = False
                                    tool_iterations = 0
                                    continue
                                else:
                                    break

                            if not tool_called:
                                break

                            audio.play("tool")
                            tool_iterations += 1
                            await asyncio.sleep(0.2)

                        if state.current_response and state.current_response.strip():
                            if state.messages and state.messages[-1].get("role") == "tool":
                                state.messages.append({"role": "assistant", "content": state.current_response})
                                await state.add_message("assistant", state.current_response)
                            elif not (state.messages and state.messages[-1].get("tool_calls")):
                                await state.add_message("assistant", state.current_response)

                            audio.play("success")

                        state.avatar_state = "idle"
                        state.status = "DONE"
                        update_layout(layout, state, console, render_chat_streaming, render_stats_panel)
                        await asyncio.sleep(0.3)

                    except (EOFError, KeyboardInterrupt):
                        break


    except KeyboardInterrupt:
        console.print(f"\n[{Colors.DIM}]MANUAL OVERRIDE: TERMINATED[/]")
    except Exception as e:
        console.print(f"\n[{Colors.ERROR}]❌ CRITICAL FAILURE: {e}[/]")
        console.print(traceback.format_exc())
    finally:
        try:
            await client.close()
        except Exception:
            pass
        
        if state.use_memory and state.session_manager and state.session_manager.store:
            try:
                await state.session_manager.store.close()
            except Exception:
                pass
        
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass
        
        console.print("\n[dim]SESSION ENDED[/]")


def main():
    """Sync entry point for console script"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

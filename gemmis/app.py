"""
GEMMIS CLI - Textual Application
# Verified OMEGA Update
"""
import asyncio
import json
import os
import signal
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Input, TabbedContent, TabPane, Footer, Static
from textual.containers import Vertical, Horizontal
from textual import on

from .state import AppState
from .ollama_client import OllamaClient
from .ui.css import get_css
from .ui.widgets.sidebar import Sidebar, ModelLoaded
from .ui.widgets.avatar import AvatarWidget
from .ui.widgets.matrix import MatrixRain
from .ui.effects import GlitchOverlay, ScanlineOverlay
from .ui.widgets.particles import ParticleSystem
from .ui.widgets.dashboard import Dashboard, ProcessKilled
from .ui.widgets.docker import Docker
from .ui.widgets.chat import Chat
from .config import MODEL_NAME, save_default_config
from .audio import get_audio

class GemmisApp(App):
    """Main Textual App for GEMMIS"""
    
    CSS = get_css()
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+m", "toggle_matrix", "Matrix"),
        ("ctrl+g", "trigger_glitch", "Glitch")
    ]

    def __init__(self, model_name: str = None, persona: str = "default"):
        super().__init__()
        self.model_name = model_name or MODEL_NAME
        self.persona = persona
        self.app_state = AppState()
        self.client = OllamaClient(model=self.model_name)
        self.is_generating = False
        self.audio = get_audio()
        
    def compose(self) -> ComposeResult:
        yield Static("╔═ GEMMIS_OS v3.0 ════════════════════════╗", id="hud-top", classes="hud")
        yield MatrixRain()
        yield GlitchOverlay(id="glitch-overlay")
        yield ScanlineOverlay(classes="scanline", id="scanline-overlay")
        yield ParticleSystem(id="particles")
        with Horizontal():
            yield Sidebar(self.app_state, self.client)
            with Vertical(id="main-area"):
                with TabbedContent(id="main-tabs"):
                    with TabPane(" Chat ", id="tab-chat"):
                        yield Chat()
                    with TabPane(" Dashboard ", id="tab-dashboard"):
                        yield Dashboard()
                    with TabPane(" Docker ", id="tab-docker"):
                        yield Docker()
                yield Input(placeholder="Enter command to execute...", id="message-input")
        yield Static("╚══ [STATUS: ONLINE] ══ [NET: SECURE] ══ [CORE: STABLE] ══╝", id="hud-bottom", classes="hud")
        yield Footer()

    async def on_mount(self) -> None:
        self.title = "GEMMIS TERMINAL v3.0"
        self.query_one("#message-input").focus()
        
        # Audio System Online
        if self.audio.enabled:
            self.audio.play("startup")
            self.notify("Audio System: ONLINE")
            
        if self.persona != "default":
            from .personas import get_persona_prompt
            self.app_state.system_prompt = get_persona_prompt(self.persona)
        await self.init_memory()
        await self.load_chat_history()
        
        # Start breathing pulse
        self.run_worker(self.breathing_pulse())
        # Start border animation
        self.set_interval(0.5, self.animate_borders)

    def animate_borders(self):
        """Rotates border colors to create an energy loop."""
        try:
            sidebar = self.query_one("Sidebar")
            if sidebar.has_class("phase-1"):
                sidebar.remove_class("phase-1")
                sidebar.add_class("phase-2")
            elif sidebar.has_class("phase-2"):
                sidebar.remove_class("phase-2")
                sidebar.add_class("phase-3")
            else:
                sidebar.remove_class("phase-3")
                sidebar.add_class("phase-1")
        except:
            pass

    async def init_memory(self):
        """Initialize persistence layer"""
        try:
            from .memory import Store, SessionManager
            gemmis_config_dir = Path.home() / ".config" / "gemmis-cli"
            db_path = gemmis_config_dir / "memory.db"
            gemmis_config_dir.mkdir(parents=True, exist_ok=True)
            store = Store(str(db_path))
            await store.connect()
            session_manager = SessionManager(store)
            session_id = await session_manager.create_session(f"GEMMIS Session - {self.model_name}")
            self.app_state.session_manager = session_manager
            self.app_state.current_session_id = session_id
            self.app_state.use_memory = True
        except Exception as e:
            self.notify(f"Memory init failed: {e}", severity="warning")
            self.app_state.use_memory = False

    async def load_chat_history(self):
        """Load messages from state into UI"""
        chat = self.query_one(Chat)
        await self.app_state.get_chat_messages()
        if not self.app_state.messages:
            chat.add_message("assistant", "Greetings. Systems Online. Neural Interface Ready.")
            return
        for msg in self.app_state.messages:
            if msg.get("role") != "system":
                chat.add_message(msg.get("role"), msg.get("content", ""))

    async def breathing_pulse(self):
        """Make the UI 'breathe' by pulsing borders.
        Also handles the 'thinking' animation for the Chat window."""
        phase = 0
        while True:
            try:
                # 1. Handle Thinking Animation (Fast Cycle)
                if self.is_generating:
                    try:
                        chat_display = self.query_one(Chat).query_one("#chat-display")

                        # Cycle phases
                        classes = ["phase-1", "phase-2", "phase-3"]
                        current_class = classes[phase % 3]
                        prev_class = classes[(phase - 1) % 3]

                        chat_display.remove_class(prev_class)
                        chat_display.add_class(current_class)

                        phase += 1
                    except Exception:
                        pass
                    await asyncio.sleep(0.2)
                    continue

                # 2. Handle Idle Breathing (Slow Pulse)
                else:
                    # Clean up phase classes if any
                    try:
                        chat_display = self.query_one(Chat).query_one("#chat-display")
                        chat_display.remove_class("phase-1")
                        chat_display.remove_class("phase-2")
                        chat_display.remove_class("phase-3")
                    except:
                        pass

                    # Pulse the sidebar and input borders
                    sidebar = self.query_one(Sidebar)
                    input_field = self.query_one("#message-input")

                    sidebar.add_class("pulse")
                    input_field.add_class("pulse")
                    await asyncio.sleep(1.0)
                    sidebar.remove_class("pulse")
                    input_field.remove_class("pulse")
                    await asyncio.sleep(1.0)
            except Exception:
                await asyncio.sleep(5)

    def action_trigger_glitch(self) -> None:
        """Manual glitch trigger"""
        self.query_one(GlitchOverlay).trigger(0.3, 0.15)

    def update_avatar(self, state: str):
        """Helper to update avatar state safely"""
        try:
            avatar = self.query_one(AvatarWidget)
            avatar.set_state(state)
            if state in ["error", "thinking"]:
                self.query_one(GlitchOverlay).trigger(0.2, 0.1)
        except Exception:
            pass # Avatar might not be mounted yet or found

    async def generate_response(self):
        """Worker to handle LLM streaming"""
        self.is_generating = True
        chat = self.query_one(Chat)
        
        # We start with thinking, then switch to speaking on first token
        self.update_avatar("thinking")
        
        try:
            full_response = ""
            first_token_received = False
            token_count = 0
            
            async for token, stats, tool_info in self.client.chat_stream(
                await self.app_state.get_chat_messages()
            ):
                if tool_info:
                    # Handle tool output
                    tool_name = tool_info.get("tool_name")
                    tool_result = tool_info.get("result", {})
                    
                    if tool_name == "generate_image" and tool_result.get("success"):
                        # Show ASCII art in chat
                        ascii_art = tool_result.get("ascii", "")
                        if ascii_art:
                            chat.add_message("assistant", f"IMAGE_UPLINK: Rendering visual data...\n```ascii\n{ascii_art}\n```")
                    
                    # Add tool result to state so LLM can see it
                    await self.app_state.add_message("tool", json.dumps(tool_result), tool_name=tool_name)

                if not first_token_received and token:
                    self.update_avatar("speaking")
                    first_token_received = True
                    
                if token:
                    full_response += token
                    token_count += 1
                    
                    # Play typing sound every few tokens to avoid audio spam
                    if token_count % 3 == 0:
                        self.audio.play("token")

            if full_response:
                chat.add_message("assistant", full_response)
                await self.app_state.add_message("assistant", full_response)
                self.audio.play("success") # Completion chime

                # Visual Feedback: Particles on Success
                try:
                    particles = self.query_one(ParticleSystem)
                    # Explode near the input area or center
                    particles.explode(50, 20, count=15, color="green")
                except:
                    pass
            
            self.update_avatar("idle")

        except Exception as e:
            self.update_avatar("error")
            self.audio.play("error")
            chat.add_message("assistant", f"Error: {e}")
            # Reset after a delay
            await asyncio.sleep(2)
            self.update_avatar("idle")
            
        finally:
            self.is_generating = False

    @on(ModelLoaded)
    def on_model_loaded(self, event: ModelLoaded):
        self.client.model = event.model_name
        self.model_name = event.model_name
        self.notify(f"Neural Core reconfigured to {event.model_name}")
        chat = self.query_one(Chat)
        chat_display = chat.query_one("#chat-display")
        # Remove all chat bubbles
        for widget in chat_display.query("*"):
            widget.remove()
        chat.add_message("assistant", f"Core switched to {event.model_name}. Reloading personality matrix...")
        self.update_avatar("idle")

    @on(ProcessKilled)
    def on_process_killed(self, event: ProcessKilled):
        try:
            # 1. Visual & Audio Feedback
            try:
                particles = self.query_one(ParticleSystem)
                particles.explode(x=40, y=10, count=15, color="red")
                if self.audio.enabled:
                    self.audio.play("break_glass")
            except:
                pass

            # 2. Execute Kill
            os.kill(event.pid, signal.SIGKILL)
            self.notify(f"TARGET {event.pid} NEUTRALIZED.")

            # Refresh Dashboard immediately
            try:
                self.query_one(Dashboard).refresh_stats()
            except Exception:
                pass
        except Exception as e:
            self.notify(f"Execution failed: {e}", severity="error")

    def action_toggle_matrix(self) -> None:
        """Toggle the Matrix rain screensaver"""
        matrix = self.query_one(MatrixRain)
        matrix.display = not matrix.display
        if matrix.display:
            self.notify("Neural Overlay: ACTIVE")
            self.audio.play("success")
        else:
            self.notify("Neural Overlay: DEACTIVATED")

def async_main(
    model: str | None = None,
    theme: str = "synthwave",
    persona: str = "default",
    minimal: bool = False,
    debug: bool = False,
    no_screen: bool = False,
) -> None:
    """Entry point for GEMMIS CLI"""
    save_default_config()
    
    # Set theme
    from .ui.theme import set_theme
    set_theme(theme)
    
    # Update App CSS with theme variables
    GemmisApp.CSS = get_css()
    
    # Show boot animation unless minimal mode
    if not minimal:
        from rich.console import Console
        from .ui.boot import run_boot_sequence
        console = Console()
        run_boot_sequence(console, theme)
    
    # Create and run app
    app = GemmisApp(model_name=model, persona=persona)
    app.run()


def main():
    save_default_config()
    app = GemmisApp()
    app.run()

if __name__ == "__main__":
    main()
"""
GEMMIS CLI - Textual Application
"""
import asyncio
import json
import os
import signal
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Input, TabbedContent, TabPane, Footer
from textual.containers import Vertical, Horizontal
from textual import on

from .state import AppState
from .ollama_client import OllamaClient
from .ui.css import get_css
from .ui.widgets.sidebar import Sidebar, ModelLoaded
from .ui.widgets.dashboard import Dashboard, ProcessKilled
from .ui.widgets.docker import Docker
from .ui.widgets.chat import Chat
from .config import MODEL_NAME, save_default_config

class GemmisApp(App):
    """Main Textual App for GEMMIS"""
    
    CSS = get_css()
    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self, model_name: str = None, persona: str = "default"):
        super().__init__()
        self.model_name = model_name or MODEL_NAME
        self.persona = persona
        self.app_state = AppState()
        self.client = OllamaClient(model=self.model_name)
        self.is_generating = False
        
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Sidebar(self.app_state, self.client)
            with Vertical(id="main-area"):
                with TabbedContent(id="main-tabs"):
                    with TabPane("Chat", id="tab-chat"):
                        yield Chat()
                    with TabPane("Dashboard", id="tab-dashboard"):
                        yield Dashboard()
                    with TabPane("Docker", id="tab-docker"):
                        yield Docker()
                yield Input(placeholder="Enter command...", id="message-input")
        yield Footer()

    async def on_mount(self) -> None:
        self.title = "GEMMIS TERMINAL"
        self.query_one("#message-input").focus()
        if self.persona != "default":
            from .personas import get_persona_prompt
            self.app_state.system_prompt = get_persona_prompt(self.persona)
        await self.init_memory()
        await self.load_chat_history()

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
            chat.add_message("assistant", "Greetings. Systems Online.")
            return
        for msg in self.app_state.messages:
            if msg.get("role") != "system":
                chat.add_message(msg.get("role"), msg.get("content", ""))

    @on(Input.Submitted, "#message-input")
    async def handle_input(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        if not user_input or self.is_generating:
            return
        event.input.value = ""
        self.query_one(Chat).add_message("user", user_input)
        await self.app_state.add_message("user", user_input)
        self.run_worker(self.generate_response(), exclusive=True)

    async def generate_response(self):
        """Worker to handle LLM streaming"""
        self.is_generating = True
        chat = self.query_one(Chat)
        try:
            full_response = ""
            # The streaming logic can be complex. For this refactor, we'll
            # just append the full response at the end.
            async for token, _, _ in self.client.chat_stream(
                await self.app_state.get_chat_messages()
            ):
                if token:
                    full_response += token

            if full_response:
                chat.add_message("assistant", full_response)
                await self.app_state.add_message("assistant", full_response)

        except Exception as e:
            chat.add_message("assistant", f"Error: {e}")
        finally:
            self.is_generating = False

    @on(ModelLoaded)
    def on_model_loaded(self, event: ModelLoaded):
        self.client.model = event.model_name
        self.model_name = event.model_name
        self.notify(f"Model set to {event.model_name}")
        chat = self.query_one(Chat)
        chat_display = chat.query_one("#chat-display")
        # Remove all chat bubbles
        for widget in chat_display.query("*"):
            widget.remove()
        chat.add_message("assistant", f"Model switched to {event.model_name}. How can I help?")

    @on(ProcessKilled)
    def on_process_killed(self, event: ProcessKilled):
        try:
            os.kill(event.pid, signal.SIGKILL)
            self.notify(f"Process {event.pid} killed.")
            self.query_one(Dashboard).refresh_table()
        except Exception as e:
            self.notify(f"Failed to kill process {event.pid}: {e}", severity="error")

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

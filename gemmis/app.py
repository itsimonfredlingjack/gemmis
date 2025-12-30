"""
GEMMIS CLI - Textual Application
"""

import asyncio
import json
import pyperclip
import traceback
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Input, TabbedContent, TabPane, Markdown, Button, Label, Static
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen, Screen
from textual.worker import Worker, get_current_worker
from textual import on

from .state import AppState
from .ollama_client import OllamaClient
from .ui.css import get_css
from .ui.widgets.sidebar import Sidebar
from .ui.widgets.dashboard import ProcessList
from .ui.widgets.docker import DockerStatus
from .ui.widgets.chat import ChatBubble, CodeBlock, SaveCodeRequest, ApplyFileModal
from .ui.widgets.avatar import AvatarWidget
from .ui import theme as theme_module
from .config import MODEL_NAME, save_default_config
from .audio import get_audio

# Modal for Tool Confirmation
class ToolConfirmationModal(ModalScreen[bool]):
    def __init__(self, tool_name: str, args: dict):
        super().__init__()
        self.tool_name = tool_name
        self.args = args

    def compose(self) -> ComposeResult:
        args_str = json.dumps(self.args, indent=2)
        with Vertical(id="tool-dialog"):
            yield Label(f"[bold yellow]⚠ PERMISSION REQUEST[/]\n\nTool: [bold]{self.tool_name}[/]")
            yield Markdown(f"```json\n{args_str}\n```")
            with Horizontal():
                yield Button("ALLOW", variant="success", id="btn-allow")
                yield Button("DENY", variant="error", id="btn-deny")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-allow":
            self.dismiss(True)
        else:
            self.dismiss(False)


class GemmisApp(App):
    """Main Textual App for GEMMIS"""
    
    CSS = ""
    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self, model_name: str = None, persona: str = "default"):
        super().__init__()
        self.model_name = model_name
        self.persona = persona
        self.app_state = AppState()
        self.client = OllamaClient(model=model_name)
        self.is_generating = False
        self.audio = get_audio()
        
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Sidebar(self.app_state)

            with Vertical(id="main-area"):
                with TabbedContent():
                    with TabPane("Neural Interface", id="tab-chat"):
                        with Vertical(id="chat-container"):
                             # Initial greeting placeholder
                             yield ChatBubble("assistant", "Initializing...")

                    with TabPane("Ops Center", id="tab-ops"):
                        yield ProcessList()

                    with TabPane("Docker", id="tab-docker"):
                        yield DockerStatus()

                yield Input(placeholder="Enter command...", id="main-input")

    async def on_mount(self) -> None:
        self.title = "GEMMIS TERMINAL"

        # Focus Input
        self.query_one("#main-input").focus()

        # Setup Persona
        if self.persona != "default":
            from .personas import get_persona_prompt
            self.app_state.system_prompt = get_persona_prompt(self.persona)

        # Initialize Memory System
        await self.init_memory()

        # Load History UI
        await self.load_chat_history()

    async def init_memory(self):
        """Initialize persistence layer"""
        try:
            from .memory import Store, SessionManager, VectorStore, CHROMADB_AVAILABLE

            gemmis_config_dir = Path.home() / ".config" / "gemmis-cli"
            db_path = gemmis_config_dir / "memory.db"
            gemmis_config_dir.mkdir(parents=True, exist_ok=True)

            store = Store(str(db_path))
            await store.connect()

            vector_store = None
            if CHROMADB_AVAILABLE:
                try:
                    vector_store = VectorStore()
                    await vector_store.initialize()
                except Exception:
                    pass

            session_manager = SessionManager(store, vector_store)
            effective_model = self.model_name if self.model_name else MODEL_NAME
            session_id = await session_manager.create_session(f"GEMMIS Session - {effective_model}")

            self.app_state.session_manager = session_manager
            self.app_state.current_session_id = session_id
            self.app_state.use_memory = True

        except Exception as e:
            self.notify(f"Memory init failed: {e}", severity="warning")
            self.app_state.use_memory = False

    async def load_chat_history(self):
        """Load messages from state into UI"""
        container = self.query_one("#chat-container", Vertical)

        # Clear placeholder
        await container.remove_children()

        # Get context loads from DB into state.messages
        # But get_chat_messages returns formatted for Ollama (dicts).
        # We want internal message objects if possible, or just use what's in state.messages after loading

        # Trigger load from DB
        await self.app_state.get_chat_messages()

        # If no messages, show greeting
        if not self.app_state.messages:
             container.mount(ChatBubble("assistant", "Greetings. Systems Online."))
             return

        # Render messages
        for msg in self.app_state.messages:
            role = msg.get("role")
            content = msg.get("content")

            # Skip system messages
            if role == "system":
                continue

            # Handle tool calls/results display
            if role == "tool":
                 name = msg.get("name", "Tool")
                 container.mount(ChatBubble("tool", f"🔧 {name} -> {content}"))
                 continue

            if role == "assistant" and "tool_calls" in msg:
                # This is the request to call a tool
                # We can show it or hide it. showing it helps context.
                for tc in msg.get("tool_calls", []):
                    func = tc.get("function", {})
                    name = func.get("name")
                    args = func.get("arguments")
                    container.mount(ChatBubble("tool", f"🔧 Calling: {name}({args})"))
                continue

            if content:
                container.mount(ChatBubble(role, content))

        container.scroll_end(animate=False)

    def copy_to_clipboard(self, text: str):
        """Copy text to system clipboard"""
        try:
            pyperclip.copy(text)
        except Exception as e:
            self.notify(f"Clipboard error: {e}", severity="error")

    @on(Input.Submitted, "#main-input")
    async def handle_input(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        if not user_input:
            return

        event.input.value = ""

        # Add User Message to UI and State
        container = self.query_one("#chat-container", Vertical)
        container.mount(ChatBubble("user", user_input))
        container.scroll_end(animate=False)

        await self.app_state.add_message("user", user_input)

        # Start Generation
        self.run_worker(self.generate_response(), exclusive=True)

    async def generate_response(self):
        """Worker to handle LLM streaming"""
        self.is_generating = True

        # Update Avatar State
        avatar = self.query_one(AvatarWidget)
        avatar.state = "thinking"

        container = self.query_one("#chat-container", Vertical)

        # Create a temporary Markdown widget for streaming
        stream_widget = Markdown("")
        container.mount(stream_widget)
        container.scroll_end(animate=False)

        full_response = ""

        try:
            # Custom tool executor wrapper for the modal
            async def tool_executor_wrapper(tool_call, tool_name, tool_args):
                # Check sensitivity
                from .tools import is_sensitive
                if not is_sensitive(tool_name, tool_args):
                    return True

                # Ask user permission via modal
                can_run = await self.push_screen_wait(ToolConfirmationModal(tool_name, tool_args))
                return can_run

            async for token, stats, tool_info in self.client.chat_stream(
                await self.app_state.get_chat_messages(),
                tool_executor=tool_executor_wrapper
            ):
                if tool_info and tool_info.get("type") == "tool_call":
                     # Handle tool call display
                     t_name = tool_info.get("tool_name")
                     t_args = tool_info.get("arguments")
                     t_res = tool_info.get("result")

                     # Update State with the Tool Call (Assistant Request)
                     # We reconstruct the message format Ollama expects
                     # Note: In a real stream, we get the call, then execution happens, then result.
                     # The `tool_info` here comes AFTER execution from our client wrapper.

                     # 1. Add Assistant Message with Tool Calls
                     tool_call_msg = {
                         "role": "assistant",
                         "content": None,
                         "tool_calls": [{
                             "type": "function",
                             "function": {
                                 "name": t_name,
                                 "arguments": json.dumps(t_args) if t_args else "{}"
                             }
                         }]
                     }
                     # We append to in-memory list directly to keep context for next turn in this loop?
                     # Ideally `add_message` supports tool_calls, but it takes (role, content).
                     # We'll manually append to `self.app_state.messages` and `session_manager`.
                     self.app_state.messages.append(tool_call_msg)
                     if self.app_state.use_memory:
                         # SessionManager might need update to support tool calls properly if strict schemas
                         # For now we rely on in-memory for the session duration
                         pass

                     container.mount(ChatBubble("tool", f"🔧 EXEC: {t_name}"))

                     # 2. Add Tool Result Message
                     tool_res_msg = {
                         "role": "tool",
                         "name": t_name,
                         "content": json.dumps(t_res, ensure_ascii=False)
                     }
                     self.app_state.messages.append(tool_res_msg)

                     container.mount(ChatBubble("tool", f"🔧 RESULT: {json.dumps(t_res, indent=2)}"))
                     container.scroll_end(animate=False)

                if token:
                    full_response += token
                    stream_widget.update(full_response)
                    container.scroll_end(animate=False)

                    # Update Avatar to speaking if not already
                    if avatar.state != "speaking":
                        avatar.state = "speaking"

                    # Optional: Audio blip per token (throttled)
                    import random
                    if random.random() < 0.2:
                        self.audio.play("token")

            # Streaming done. Replace Markdown widget with parsed ChatBubble
            stream_widget.remove()
            if full_response:
                container.mount(ChatBubble("assistant", full_response))
                await self.app_state.add_message("assistant", full_response)

        except Exception as e:
            container.mount(ChatBubble("error", f"Error: {e}"))
            avatar.state = "error"

        finally:
            self.is_generating = False
            if avatar.state != "error":
                avatar.state = "idle"
            container.scroll_end()

    @on(SaveCodeRequest)
    def on_save_code_request(self, message: SaveCodeRequest):
        """Handle request to save code from a ChatWidget"""
        def handle_save(filepath: str):
            if filepath:
                from .tools import write_file
                res = write_file(filepath, message.code)
                if "error" in res:
                    self.notify(f"Error: {res['error']}", severity="error")
                else:
                    self.notify(f"Saved to {filepath}", severity="information")

        self.push_screen(ApplyFileModal(message.code), handle_save)


async def async_main(
    model: str | None = None,
    theme: str = "synthwave",
    persona: str = "default",
    minimal: bool = False,
    debug: bool = False,
    no_screen: bool = False,
) -> None:
    """Main application loop"""

    # Initialize Config
    save_default_config()
    if model:
        from . import config
        config.MODEL_NAME = model

    # Set Theme
    theme_module.set_theme(theme)

    # Inject CSS based on selected theme
    GemmisApp.CSS = get_css()

    app = GemmisApp(model_name=model, persona=persona)
    await app.run_async()

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

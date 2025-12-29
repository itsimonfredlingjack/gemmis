"""
GEMMIS CLI - Application State Management
"""

from dataclasses import dataclass, field
from typing import Optional

from .config import SYSTEM_PROMPT


@dataclass
class AppState:
    """Application state"""

    messages: list[dict] = field(default_factory=list)
    system_prompt: str = SYSTEM_PROMPT
    connected: bool = False
    status: str = "READY"
    avatar_state: str = "idle"  # idle, thinking, speaking
    current_response: str = ""
    tokens: int = 0
    tokens_per_sec: float = 0.0
    system_stats: dict = field(default_factory=dict)

    # History for sparklines (store last 20 values)
    cpu_history: list[float] = field(default_factory=list)
    mem_history: list[float] = field(default_factory=list)
    tokens_per_sec_history: list[float] = field(default_factory=list)

    # Visual Effects State
    effects: dict = field(default_factory=dict)

    # Memory system (optional, initialized in app.py)
    session_manager: Optional[object] = None
    current_session_id: Optional[str] = None
    use_memory: bool = True  # Enable/disable persistent memory

    async def add_message(self, role: str, content: str):
        """Add message to both in-memory list and persistent storage"""
        self.messages.append({"role": role, "content": content})
        
        # Save to persistent storage if memory is enabled
        if self.use_memory and self.session_manager and self.current_session_id:
            try:
                await self.session_manager.add_message(role, content)
            except Exception:
                # Silently fail if memory system has issues
                pass

    async def get_chat_messages(self) -> list[dict]:
        """Get messages in Ollama format with system prompt and current system stats"""
        # Load messages from persistent storage if available
        if self.use_memory and self.session_manager and self.current_session_id:
            try:
                context = await self.session_manager.get_context()
                # Convert Message objects to dict format
                self.messages = [
                    {"role": msg.role, "content": msg.content}
                    for msg in context
                    if msg.role != "system"  # Exclude system messages from context
                ]
            except Exception:
                # Fall back to in-memory messages if memory system fails
                pass

        # Add system context to prompt
        system_context = self.system_prompt
        if self.system_stats:
            cpu = self.system_stats.get("cpu", {})
            memory = self.system_stats.get("memory", {})

            context_parts = []
            if cpu:
                context_parts.append(f"CPU: {cpu.get('usage', 0):.1f}%")
            if memory:
                context_parts.append(
                    f"RAM: {memory.get('percent', 0):.1f}% ({memory.get('used', 0) / (1024**3):.1f}GB/{memory.get('total', 0) / (1024**3):.1f}GB)"
                )

            if context_parts:
                system_context += f"\n\nAktuell systemstatus: {', '.join(context_parts)}"

        msgs = [{"role": "system", "content": system_context}]

        # Convert messages, handling tool calls
        for m in self.messages:
            msg = {"role": m["role"]}
            if "tool_calls" in m:
                msg["tool_calls"] = m["tool_calls"]
                msg["content"] = None
            else:
                msg["content"] = m.get("content", "")
            msgs.append(msg)

        return msgs

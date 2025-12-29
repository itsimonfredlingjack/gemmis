"""Session management with context window handling and memory compression."""

import uuid
from datetime import datetime
from typing import Any, Optional

from .store import Store
from .vectors import VectorStore, CHROMADB_AVAILABLE


class Message:
    """Message data structure."""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ):
        """Initialize a message.

        Args:
            role: Message role (user, assistant, system, etc.)
            content: Message content
            timestamp: ISO timestamp (defaults to now)
            metadata: Optional metadata
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata")
        )


class SessionManager:
    """Manages conversation sessions with memory and context."""

    def __init__(
        self,
        store: Store,
        vector_store: Optional[VectorStore] = None,
        max_context_messages: int = 50,
        max_context_tokens: int = 4000
    ):
        """Initialize the session manager.

        Args:
            store: Storage backend
            vector_store: Optional vector store for semantic search
            max_context_messages: Maximum messages to keep in context
            max_context_tokens: Approximate max tokens in context
        """
        self.store = store
        self.vector_store = vector_store
        self.max_context_messages = max_context_messages
        self.max_context_tokens = max_context_tokens
        self._current_session_id: Optional[str] = None

    async def create_session(
        self,
        name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """Create a new session.

        Args:
            name: Session name (auto-generated if None)
            metadata: Optional session metadata

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session_name = name or f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"

        await self.store.create_session(
            session_id=session_id,
            name=session_name,
            metadata=metadata
        )

        self._current_session_id = session_id
        return session_id

    async def load_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Load an existing session.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        session = await self.store.get_session(session_id)
        if session:
            self._current_session_id = session_id
        return session

    async def get_current_session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self._current_session_id

    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """List all sessions.

        Args:
            limit: Maximum number of sessions
            offset: Number of sessions to skip

        Returns:
            List of sessions
        """
        return await self.store.list_sessions(limit=limit, offset=offset)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted
        """
        # Delete from vector store if available
        if self.vector_store:
            await self.vector_store.delete_by_metadata({"session_id": session_id})

        # Delete from store
        result = await self.store.delete_session(session_id)

        if session_id == self._current_session_id:
            self._current_session_id = None

        return result

    async def add_message(
        self,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> int:
        """Add a message to the current or specified session.

        Args:
            role: Message role
            content: Message content
            session_id: Session ID (uses current if None)
            metadata: Optional metadata

        Returns:
            Message ID

        Raises:
            ValueError: If no session is active
        """
        sid = session_id or self._current_session_id
        if not sid:
            raise ValueError("No active session. Create or load a session first.")

        # Add to store
        message_id = await self.store.add_message(
            session_id=sid,
            role=role,
            content=content,
            metadata=metadata
        )

        # Add to vector store for semantic search
        if self.vector_store and role in ("user", "assistant"):
            vector_metadata = {
                "session_id": sid,
                "role": role,
                "message_id": str(message_id),
                **(metadata or {})
            }
            await self.vector_store.add_message(
                message_id=f"{sid}:{message_id}",
                content=content,
                metadata=vector_metadata
            )

        return message_id

    async def get_messages(
        self,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> list[Message]:
        """Get messages from a session.

        Args:
            session_id: Session ID (uses current if None)
            limit: Maximum messages to retrieve
            offset: Number of messages to skip

        Returns:
            List of messages
        """
        sid = session_id or self._current_session_id
        if not sid:
            return []

        messages_data = await self.store.get_messages(
            session_id=sid,
            limit=limit,
            offset=offset
        )

        return [Message.from_dict(msg) for msg in messages_data]

    async def get_context(
        self,
        session_id: Optional[str] = None,
        include_system: bool = True
    ) -> list[Message]:
        """Get conversation context for the current session.

        Implements basic context window management by keeping the most
        recent messages within token limits.

        Args:
            session_id: Session ID (uses current if None)
            include_system: Include system messages

        Returns:
            List of messages for context
        """
        messages = await self.get_messages(session_id=session_id)

        if not include_system:
            messages = [msg for msg in messages if msg.role != "system"]

        # Simple context management: keep most recent messages
        if len(messages) > self.max_context_messages:
            # Keep system messages + recent messages
            system_msgs = [msg for msg in messages if msg.role == "system"]
            other_msgs = [msg for msg in messages if msg.role != "system"]

            # Keep most recent other messages
            recent_count = self.max_context_messages - len(system_msgs)
            if recent_count > 0:
                messages = system_msgs + other_msgs[-recent_count:]
            else:
                messages = system_msgs[:self.max_context_messages]

        return messages

    async def compress_context(
        self,
        session_id: Optional[str] = None,
        keep_recent: int = 10
    ) -> int:
        """Compress old messages by summarizing or removing them.

        Args:
            session_id: Session ID (uses current if None)
            keep_recent: Number of recent messages to keep

        Returns:
            Number of messages removed
        """
        sid = session_id or self._current_session_id
        if not sid:
            return 0

        messages = await self.get_messages(session_id=sid)

        if len(messages) <= keep_recent:
            return 0

        # Calculate timestamp threshold
        messages_to_keep = messages[-keep_recent:]
        threshold_timestamp = messages_to_keep[0].timestamp if messages_to_keep else None

        if not threshold_timestamp:
            return 0

        # Delete old messages from store
        deleted = await self.store.delete_messages(
            session_id=sid,
            before_timestamp=threshold_timestamp
        )

        return deleted

    async def find_relevant_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_results: int = 5
    ) -> list[dict[str, Any]]:
        """Find relevant context using semantic search.

        Args:
            query: Search query
            session_id: Session ID (uses current if None)
            max_results: Maximum results to return

        Returns:
            List of relevant messages

        Raises:
            RuntimeError: If vector store is not available
        """
        if not self.vector_store:
            raise RuntimeError("Vector store is not configured")

        sid = session_id or self._current_session_id

        return await self.vector_store.find_context(
            query=query,
            session_id=sid,
            max_results=max_results
        )

    async def log_agent_action(
        self,
        agent_name: str,
        action: str,
        details: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> int:
        """Log an agent action.

        Args:
            agent_name: Name of the agent
            action: Action performed
            details: Optional action details
            session_id: Session ID (uses current if None)

        Returns:
            Log entry ID

        Raises:
            ValueError: If no session is active
        """
        sid = session_id or self._current_session_id
        if not sid:
            raise ValueError("No active session")

        return await self.store.log_agent_action(
            session_id=sid,
            agent_name=agent_name,
            action=action,
            details=details
        )

    async def get_agent_logs(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get agent logs.

        Args:
            agent_name: Filter by agent name
            session_id: Session ID (uses current if None)
            limit: Maximum logs to return

        Returns:
            List of log entries
        """
        sid = session_id or self._current_session_id
        if not sid:
            return []

        return await self.store.get_agent_logs(
            session_id=sid,
            agent_name=agent_name,
            limit=limit
        )

    async def get_session_summary(
        self,
        session_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Get summary statistics for a session.

        Args:
            session_id: Session ID (uses current if None)

        Returns:
            Session summary
        """
        sid = session_id or self._current_session_id
        if not sid:
            return {}

        session = await self.store.get_session(sid)
        if not session:
            return {}

        messages = await self.get_messages(session_id=sid)

        # Count by role
        role_counts = {}
        for msg in messages:
            role_counts[msg.role] = role_counts.get(msg.role, 0) + 1

        return {
            "session_id": sid,
            "name": session["name"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "message_count": len(messages),
            "messages_by_role": role_counts,
            "metadata": session["metadata"]
        }

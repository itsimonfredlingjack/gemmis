"""
Base memory store for Legion agents.

Provides a simple in-memory storage with optional persistence
for agent context and conversation history.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """
    A single entry in the memory store.

    Attributes:
        id: Unique identifier for this entry.
        key: Lookup key for the entry.
        value: The stored value (any JSON-serializable data).
        entry_type: Category of memory (context, fact, conversation, etc.).
        agent_id: ID of the agent that created this entry.
        session_id: Session identifier for grouping entries.
        created_at: When the entry was created.
        expires_at: Optional expiration time.
        metadata: Additional entry metadata.
        importance: Importance score for retrieval ranking (0.0-1.0).
    """

    id: UUID = Field(default_factory=uuid4)
    key: str
    value: Any
    entry_type: str = "general"
    agent_id: str | None = None
    session_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    importance: float = 0.5

    @property
    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class MemoryStore:
    """
    In-memory storage for agent context and data.

    Provides a simple key-value store with support for
    namespacing, TTL, and basic retrieval operations.

    Example:
        store = MemoryStore()
        await store.store("user_name", "Alice", namespace="session")
        name = await store.retrieve("user_name", namespace="session")
    """

    def __init__(self, max_entries: int = 10000) -> None:
        """
        Initialize the memory store.

        Args:
            max_entries: Maximum number of entries to store.
        """
        self._entries: dict[str, MemoryEntry] = {}
        self._max_entries = max_entries

    def _make_key(self, key: str, namespace: str = "default") -> str:
        """Create a namespaced storage key."""
        return f"{namespace}:{key}"

    async def store(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        entry_type: str = "general",
        agent_id: str | None = None,
        session_id: str | None = None,
        ttl_seconds: int | None = None,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """
        Store a value in memory.

        Args:
            key: The lookup key.
            value: The value to store.
            namespace: Namespace for key isolation.
            entry_type: Category of the entry.
            agent_id: ID of the storing agent.
            session_id: Session identifier.
            ttl_seconds: Time-to-live in seconds (None for no expiry).
            importance: Importance score (0.0-1.0).
            metadata: Additional metadata.

        Returns:
            The created MemoryEntry.
        """
        # Cleanup if at capacity
        if len(self._entries) >= self._max_entries:
            await self._cleanup_expired()
            if len(self._entries) >= self._max_entries:
                await self._evict_least_important()

        expires_at = None
        if ttl_seconds is not None:
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        entry = MemoryEntry(
            key=key,
            value=value,
            entry_type=entry_type,
            agent_id=agent_id,
            session_id=session_id,
            expires_at=expires_at,
            importance=importance,
            metadata=metadata or {},
        )

        storage_key = self._make_key(key, namespace)
        self._entries[storage_key] = entry
        return entry

    async def retrieve(
        self,
        key: str,
        namespace: str = "default",
        default: Any = None,
    ) -> Any:
        """
        Retrieve a value from memory.

        Args:
            key: The lookup key.
            namespace: Namespace to search in.
            default: Default value if not found or expired.

        Returns:
            The stored value or default.
        """
        storage_key = self._make_key(key, namespace)
        entry = self._entries.get(storage_key)

        if entry is None:
            return default

        if entry.is_expired:
            del self._entries[storage_key]
            return default

        return entry.value

    async def retrieve_entry(
        self,
        key: str,
        namespace: str = "default",
    ) -> MemoryEntry | None:
        """
        Retrieve the full MemoryEntry object.

        Args:
            key: The lookup key.
            namespace: Namespace to search in.

        Returns:
            The MemoryEntry or None if not found/expired.
        """
        storage_key = self._make_key(key, namespace)
        entry = self._entries.get(storage_key)

        if entry is None:
            return None

        if entry.is_expired:
            del self._entries[storage_key]
            return None

        return entry

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete an entry from memory.

        Args:
            key: The lookup key.
            namespace: Namespace to delete from.

        Returns:
            True if entry was deleted, False if not found.
        """
        storage_key = self._make_key(key, namespace)
        if storage_key in self._entries:
            del self._entries[storage_key]
            return True
        return False

    async def list_keys(
        self,
        namespace: str = "default",
        entry_type: str | None = None,
        agent_id: str | None = None,
    ) -> list[str]:
        """
        List all keys in a namespace.

        Args:
            namespace: Namespace to list.
            entry_type: Filter by entry type.
            agent_id: Filter by agent ID.

        Returns:
            List of keys (without namespace prefix).
        """
        prefix = f"{namespace}:"
        keys = []

        for storage_key, entry in self._entries.items():
            if not storage_key.startswith(prefix):
                continue
            if entry.is_expired:
                continue
            if entry_type and entry.entry_type != entry_type:
                continue
            if agent_id and entry.agent_id != agent_id:
                continue

            # Remove namespace prefix
            keys.append(storage_key[len(prefix):])

        return keys

    async def search(
        self,
        namespace: str = "default",
        entry_type: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        min_importance: float = 0.0,
    ) -> list[MemoryEntry]:
        """
        Search for entries matching criteria.

        Args:
            namespace: Namespace to search.
            entry_type: Filter by entry type.
            agent_id: Filter by agent ID.
            session_id: Filter by session ID.
            min_importance: Minimum importance score.

        Returns:
            List of matching MemoryEntry objects.
        """
        prefix = f"{namespace}:"
        results = []

        for storage_key, entry in self._entries.items():
            if not storage_key.startswith(prefix):
                continue
            if entry.is_expired:
                continue
            if entry_type and entry.entry_type != entry_type:
                continue
            if agent_id and entry.agent_id != agent_id:
                continue
            if session_id and entry.session_id != session_id:
                continue
            if entry.importance < min_importance:
                continue

            results.append(entry)

        # Sort by importance (highest first)
        results.sort(key=lambda e: e.importance, reverse=True)
        return results

    async def clear_namespace(self, namespace: str) -> int:
        """
        Clear all entries in a namespace.

        Args:
            namespace: Namespace to clear.

        Returns:
            Number of entries deleted.
        """
        prefix = f"{namespace}:"
        keys_to_delete = [
            k for k in self._entries.keys()
            if k.startswith(prefix)
        ]

        for key in keys_to_delete:
            del self._entries[key]

        return len(keys_to_delete)

    async def clear_all(self) -> int:
        """
        Clear all entries from the store.

        Returns:
            Number of entries deleted.
        """
        count = len(self._entries)
        self._entries.clear()
        return count

    async def _cleanup_expired(self) -> int:
        """Remove all expired entries."""
        expired_keys = [
            k for k, v in self._entries.items()
            if v.is_expired
        ]

        for key in expired_keys:
            del self._entries[key]

        return len(expired_keys)

    async def _evict_least_important(self, count: int = 100) -> int:
        """Evict the least important entries."""
        if not self._entries:
            return 0

        # Sort by importance (ascending) and creation time (oldest first)
        sorted_entries = sorted(
            self._entries.items(),
            key=lambda x: (x[1].importance, x[1].created_at),
        )

        # Remove the least important entries
        to_remove = sorted_entries[:count]
        for key, _ in to_remove:
            del self._entries[key]

        return len(to_remove)

    @property
    def size(self) -> int:
        """Get the current number of entries."""
        return len(self._entries)

    def __len__(self) -> int:
        """Get the current number of entries."""
        return len(self._entries)

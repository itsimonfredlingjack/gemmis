"""SQLite-based session storage for LEGION."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import aiosqlite


class Store:
    """SQLite-based async storage for sessions, messages, and agent logs."""

    def __init__(self, db_path: str | Path = "~/.legion/storage.db"):
        """Initialize the store.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Connect to the database and create tables if needed."""
        self._db = await aiosqlite.connect(str(self.db_path))
        self._db.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_agent_logs_session
                ON agent_logs(session_id, timestamp);
        """)
        await self._db.commit()

    # Session operations
    async def create_session(
        self,
        session_id: str,
        name: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """Create a new session.

        Args:
            session_id: Unique session identifier
            name: Human-readable session name
            metadata: Optional session metadata
        """
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            """
            INSERT INTO sessions (id, name, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, name, now, now, json.dumps(metadata or {}))
        )
        await self._db.commit()

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found
        """
        async with self._db.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "name": row["name"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"])
                }
            return None

    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """List sessions ordered by last update.

        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of session data
        """
        async with self._db.execute(
            """
            SELECT * FROM sessions
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"])
                }
                for row in rows
            ]

    async def update_session(
        self,
        session_id: str,
        name: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """Update session data.

        Args:
            session_id: Session identifier
            name: New session name
            metadata: New metadata to merge

        Returns:
            True if session was updated
        """
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if metadata is not None:
            # Get current metadata and merge
            session = await self.get_session(session_id)
            if session:
                current_meta = session["metadata"]
                current_meta.update(metadata)
                updates.append("metadata = ?")
                params.append(json.dumps(current_meta))

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(session_id)

        await self._db.execute(
            f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
            params
        )
        await self._db.commit()
        return True

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all associated data.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted
        """
        cursor = await self._db.execute(
            "DELETE FROM sessions WHERE id = ?",
            (session_id,)
        )
        await self._db.commit()
        return cursor.rowcount > 0

    # Message operations
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> int:
        """Add a message to a session.

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system, etc.)
            content: Message content
            metadata: Optional message metadata

        Returns:
            Message ID
        """
        cursor = await self._db.execute(
            """
            INSERT INTO messages (session_id, role, content, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                datetime.utcnow().isoformat(),
                json.dumps(metadata or {})
            )
        )
        await self._db.commit()

        # Update session timestamp
        await self._db.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), session_id)
        )
        await self._db.commit()

        return cursor.lastrowid

    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get messages for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages (None for all)
            offset: Number of messages to skip

        Returns:
            List of messages ordered by timestamp
        """
        query = """
            SELECT * FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """
        params = [session_id]

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"],
                    "metadata": json.loads(row["metadata"])
                }
                for row in rows
            ]

    async def delete_messages(
        self,
        session_id: str,
        before_timestamp: Optional[str] = None
    ) -> int:
        """Delete messages from a session.

        Args:
            session_id: Session identifier
            before_timestamp: Delete messages before this timestamp (None for all)

        Returns:
            Number of messages deleted
        """
        if before_timestamp:
            cursor = await self._db.execute(
                """
                DELETE FROM messages
                WHERE session_id = ? AND timestamp < ?
                """,
                (session_id, before_timestamp)
            )
        else:
            cursor = await self._db.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session_id,)
            )

        await self._db.commit()
        return cursor.rowcount

    # Agent log operations
    async def log_agent_action(
        self,
        session_id: str,
        agent_name: str,
        action: str,
        details: Optional[dict[str, Any]] = None
    ) -> int:
        """Log an agent action.

        Args:
            session_id: Session identifier
            agent_name: Name of the agent
            action: Action performed
            details: Optional action details

        Returns:
            Log entry ID
        """
        cursor = await self._db.execute(
            """
            INSERT INTO agent_logs (session_id, agent_name, action, details, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                agent_name,
                action,
                json.dumps(details or {}),
                datetime.utcnow().isoformat()
            )
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_agent_logs(
        self,
        session_id: str,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get agent logs for a session.

        Args:
            session_id: Session identifier
            agent_name: Filter by agent name (None for all)
            limit: Maximum number of logs

        Returns:
            List of log entries ordered by timestamp
        """
        if agent_name:
            query = """
                SELECT * FROM agent_logs
                WHERE session_id = ? AND agent_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params = (session_id, agent_name, limit)
        else:
            query = """
                SELECT * FROM agent_logs
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params = (session_id, limit)

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "agent_name": row["agent_name"],
                    "action": row["action"],
                    "details": json.loads(row["details"]),
                    "timestamp": row["timestamp"]
                }
                for row in rows
            ]

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()

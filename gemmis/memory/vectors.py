"""ChromaDB integration for semantic search and vector storage."""

import asyncio
from typing import Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class VectorStore:
    """ChromaDB-based vector storage for semantic search."""

    def __init__(
        self,
        persist_directory: str = "~/.legion/chromadb",
        collection_name: str = "legion_memory"
    ):
        """Initialize the vector store.

        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the ChromaDB collection

        Raises:
            ImportError: If ChromaDB is not installed
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB is not installed. Install with: pip install chromadb"
            )

        from pathlib import Path
        persist_dir = Path(persist_directory).expanduser()
        persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(persist_dir)
        ))
        self.collection_name = collection_name
        self.collection = None

    async def initialize(self) -> None:
        """Initialize or get the collection."""
        # ChromaDB operations are synchronous, run in executor
        loop = asyncio.get_running_loop()
        self.collection = await loop.run_in_executor(
            None,
            lambda: self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "LEGION session memory"}
            )
        )

    async def add_message(
        self,
        message_id: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
        embedding: Optional[list[float]] = None
    ) -> None:
        """Add a message to the vector store.

        Args:
            message_id: Unique message identifier
            content: Message content to embed
            metadata: Optional metadata
            embedding: Pre-computed embedding (if None, ChromaDB will generate)
        """
        if not self.collection:
            await self.initialize()

        loop = asyncio.get_running_loop()

        if embedding:
            await loop.run_in_executor(
                None,
                lambda: self.collection.add(
                    ids=[message_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata or {}]
                )
            )
        else:
            await loop.run_in_executor(
                None,
                lambda: self.collection.add(
                    ids=[message_id],
                    documents=[content],
                    metadatas=[metadata or {}]
                )
            )

    async def add_messages_batch(
        self,
        message_ids: list[str],
        contents: list[str],
        metadatas: Optional[list[dict[str, Any]]] = None,
        embeddings: Optional[list[list[float]]] = None
    ) -> None:
        """Add multiple messages in batch.

        Args:
            message_ids: List of message IDs
            contents: List of message contents
            metadatas: Optional list of metadata dicts
            embeddings: Optional pre-computed embeddings
        """
        if not self.collection:
            await self.initialize()

        if not message_ids:
            return

        loop = asyncio.get_running_loop()
        metas = metadatas or [{}] * len(message_ids)

        if embeddings:
            await loop.run_in_executor(
                None,
                lambda: self.collection.add(
                    ids=message_ids,
                    embeddings=embeddings,
                    documents=contents,
                    metadatas=metas
                )
            )
        else:
            await loop.run_in_executor(
                None,
                lambda: self.collection.add(
                    ids=message_ids,
                    documents=contents,
                    metadatas=metas
                )
            )

    async def search_similar(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[dict[str, Any]] = None,
        where_document: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """Search for similar messages.

        Args:
            query: Query text to search for
            n_results: Number of results to return
            where: Metadata filter (e.g., {"session_id": "123"})
            where_document: Document content filter

        Returns:
            List of similar messages with metadata and distances
        """
        if not self.collection:
            await self.initialize()

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                where_document=where_document
            )
        )

        # Format results
        similar = []
        if results["ids"] and results["ids"][0]:
            for i, msg_id in enumerate(results["ids"][0]):
                similar.append({
                    "id": msg_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })

        return similar

    async def get_by_id(self, message_id: str) -> Optional[dict[str, Any]]:
        """Get a message by ID.

        Args:
            message_id: Message identifier

        Returns:
            Message data or None if not found
        """
        if not self.collection:
            await self.initialize()

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.collection.get(ids=[message_id])
        )

        if result["ids"]:
            return {
                "id": result["ids"][0],
                "content": result["documents"][0] if result["documents"] else None,
                "metadata": result["metadatas"][0] if result["metadatas"] else {},
                "embedding": result["embeddings"][0] if result.get("embeddings") else None
            }

        return None

    async def delete_message(self, message_id: str) -> None:
        """Delete a message from the vector store.

        Args:
            message_id: Message identifier
        """
        if not self.collection:
            await self.initialize()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.collection.delete(ids=[message_id])
        )

    async def delete_by_metadata(self, where: dict[str, Any]) -> None:
        """Delete messages by metadata filter.

        Args:
            where: Metadata filter (e.g., {"session_id": "123"})
        """
        if not self.collection:
            await self.initialize()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self.collection.delete(where=where)
        )

    async def count(self, where: Optional[dict[str, Any]] = None) -> int:
        """Count messages in the collection.

        Args:
            where: Optional metadata filter

        Returns:
            Number of messages
        """
        if not self.collection:
            await self.initialize()

        loop = asyncio.get_running_loop()

        if where:
            result = await loop.run_in_executor(
                None,
                lambda: self.collection.get(where=where)
            )
            return len(result["ids"])
        else:
            return await loop.run_in_executor(
                None,
                lambda: self.collection.count()
            )

    async def find_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        max_results: int = 5,
        relevance_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """Find relevant context for a query.

        Args:
            query: Query text
            session_id: Optional session ID to filter by
            max_results: Maximum number of results
            relevance_threshold: Minimum similarity score (0-1)

        Returns:
            List of relevant messages sorted by relevance
        """
        where = {"session_id": session_id} if session_id else None
        results = await self.search_similar(
            query=query,
            n_results=max_results,
            where=where
        )

        # Filter by relevance threshold (lower distance = higher relevance)
        # ChromaDB uses distance, so we convert: similarity = 1 - normalized_distance
        filtered = []
        for result in results:
            if result["distance"] is not None:
                # Assuming distance is already normalized (0-2 range for cosine)
                similarity = 1 - (result["distance"] / 2)
                if similarity >= relevance_threshold:
                    result["similarity"] = similarity
                    filtered.append(result)

        return filtered

    def reset_collection(self) -> None:
        """Delete and recreate the collection. Use with caution!"""
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass  # Collection might not exist

        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "LEGION session memory"}
        )

    async def __aenter__(self):
        """Context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # ChromaDB persists automatically
        pass

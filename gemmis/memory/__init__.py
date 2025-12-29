"""Memory module for GEMMIS - Persistent memory and context management."""

from .store import Store
from .session import SessionManager, Message

try:
    from .vectors import VectorStore, CHROMADB_AVAILABLE
except ImportError:
    VectorStore = None
    CHROMADB_AVAILABLE = False

__all__ = [
    "Store",
    "SessionManager",
    "Message",
    "VectorStore",
    "CHROMADB_AVAILABLE",
]

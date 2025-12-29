"""
GEMMIS Brain Module - Second Brain / Knowledge Base
Powered by ChromaDB and SentenceTransformers
"""

import logging
from pathlib import Path
from typing import Any

# Try to import optional dependencies
try:
    import chromadb
    from chromadb.utils import embedding_functions

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemmis_brain")

# Config
BRAIN_DIR = Path.home() / ".config" / "juridik-ai" / "brain_db"
COLLECTION_NAME = "university_of_fuckers"


class Brain:
    def __init__(self):
        if not CHROMA_AVAILABLE:
            print(
                "⚠️  VARNING: ChromaDB saknas. Kör 'pip install chromadb sentence-transformers' för att aktivera hjärnan."
            )
            self.client = None
            self.collection = None
            return

        # Ensure dir exists
        BRAIN_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=str(BRAIN_DIR))

        # Use a default embedding function (all-MiniLM-L6-v2 is fast and good)
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME, embedding_function=self.ef
        )

    def learn_from_directory(self, dir_path: str) -> dict[str, int]:
        """Scan directory and index files recursively"""
        if not self.client:
            return {"error": "ChromaDB missing"}

        root_path = Path(dir_path).expanduser().resolve()
        if not root_path.exists():
            return {"error": f"Directory not found: {root_path}"}

        print(f"🧠 GEMMIS läser in: {root_path}...")

        # Supported file types
        extensions = ["**/*.md", "**/*.txt", "**/*.py", "**/*.js", "**/*.json", "**/*.sh"]

        files_processed = 0
        chunks_added = 0

        for ext in extensions:
            for file_path in root_path.glob(ext):
                if file_path.is_file() and not any(
                    p.name.startswith(".") for p in file_path.parents
                ):
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        if not content.strip():
                            continue

                        # Simple chunking (split by paragraphs or length)
                        chunks = self._chunk_text(content, chunk_size=1000)

                        ids = [f"{file_path.name}_{i}" for i in range(len(chunks))]
                        metadatas = [
                            {"source": str(file_path), "chunk": i} for i in range(len(chunks))
                        ]

                        self.collection.upsert(documents=chunks, metadatas=metadatas, ids=ids)

                        files_processed += 1
                        chunks_added += len(chunks)
                        print(f"  📖 Läste: {file_path.name} ({len(chunks)} bitar)")

                    except Exception as e:
                        logger.error(f"Kunde inte läsa {file_path}: {e}")

        return {"files": files_processed, "chunks": chunks_added}

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> list[str]:
        """Split text into smaller chunks"""
        # Very basic chunker - split by double newlines first, then combine
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk += p + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = p + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search the brain for relevant info"""
        if not self.client or self.collection.count() == 0:
            return []

        results = self.collection.query(query_texts=[query], n_results=n_results)

        # Flatten results
        output = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                output.append(
                    {
                        "text": doc,
                        "source": meta.get("source", "unknown"),
                        "score": results.get("distances", [[0]])[0][i]
                        if results.get("distances")
                        else 0,
                    }
                )

        return output


# Global instance
_brain = None


def get_brain():
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain

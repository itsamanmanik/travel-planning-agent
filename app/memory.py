"""Agent memory.

ShortTermMemory holds the current conversation in RAM (per session).
LongTermMemory persists user preferences in a ChromaDB vector store and
retrieves them by semantic similarity, so recall works across sessions.
"""

import chromadb

from . import config


class ShortTermMemory:
    """Recent conversation messages per session, kept in memory."""

    def __init__(self, max_messages: int = config.MAX_HISTORY_MESSAGES):
        self._sessions: dict[str, list[dict]] = {}
        self._max = max_messages

    def add(self, session_id: str, role: str, content: str) -> None:
        history = self._sessions.setdefault(session_id, [])
        history.append({"role": role, "content": content})
        if len(history) > self._max:
            self._sessions[session_id] = history[-self._max:]

    def get(self, session_id: str) -> list[dict]:
        return self._sessions.get(session_id, [])


class LongTermMemory:
    """User preferences stored in a persistent ChromaDB vector collection."""

    def __init__(self, persist_dir: str = config.CHROMA_DIR):
        self._client = chromadb.PersistentClient(path=persist_dir)
        # A single collection; users are separated by the user_id metadata.
        self._collection = self._client.get_or_create_collection("preferences")

    def remember(self, user_id: str, text: str) -> None:
        """Store a preference note for a user (idempotent per note)."""
        note_id = f"{user_id}:{abs(hash(text))}"
        self._collection.upsert(
            ids=[note_id],
            documents=[text],
            metadatas=[{"user_id": user_id}],
        )

    def recall(self, user_id: str, query: str, k: int = 3) -> list[str]:
        """Return the k most relevant stored notes for this user and query."""
        results = self._collection.query(
            query_texts=[query],
            n_results=k,
            where={"user_id": user_id},
        )
        docs = results.get("documents") or [[]]
        return docs[0]

    def all_for_user(self, user_id: str) -> list[str]:
        """Return every stored note for a user."""
        results = self._collection.get(where={"user_id": user_id})
        return results.get("documents", [])

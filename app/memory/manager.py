from __future__ import annotations

from typing import Any

from app.memory.base import MemoryStore
from app.memory.episodic import get_episodic_memory
from app.memory.semantic import get_semantic_memory
from app.memory.working import get_working_memory
from common.logger import get_logger
from models.memory import MemoryEntry, MemorySearchRequest, MemorySearchResult

logger = get_logger(__name__)


class MemoryManager:
    def __init__(self) -> None:
        self.working: MemoryStore = get_working_memory()
        self.episodic: MemoryStore = get_episodic_memory()
        self.semantic: MemoryStore = get_semantic_memory()

    async def save_working(self, entry: MemoryEntry) -> None:
        entry.memory_type = "working"
        await self.working.save(entry)

    async def retrieve(self, query: str, user_id: str, top_k: int = 5) -> list[MemorySearchResult]:
        request = MemorySearchRequest(query=query, user_id=user_id, top_k=top_k)

        working_results = await self.working.search(request)
        if working_results:
            return working_results[:top_k]

        episodic_results = await self.episodic.search(request)
        if episodic_results:
            return episodic_results[:top_k]

        semantic_results = await self.semantic.search(request)
        return semantic_results[:top_k]

    async def retrieve_all_layers(
        self, query: str, user_id: str, top_k: int = 5
    ) -> dict[str, list[MemorySearchResult]]:
        request = MemorySearchRequest(query=query, user_id=user_id, top_k=top_k)

        working_task = self.working.search(request)
        episodic_task = self.episodic.search(request)
        semantic_task = self.semantic.search(request)

        return {
            "working": await working_task,
            "episodic": await episodic_task,
            "semantic": await semantic_task,
        }

    async def archive_session(self, session_id: str, user_id: str) -> None:
        from app.memory.working import WorkingMemoryStore

        if isinstance(self.working, WorkingMemoryStore):
            entries = await self.working.get_session_memories(session_id)
            for entry in entries:
                entry.user_id = user_id
                await self.episodic.save(entry)

            important_entries = [e for e in entries if e.importance >= 0.7]
            for entry in important_entries:
                await self.semantic.save(entry)

        await self.working.clear_session(session_id)

    async def add_knowledge(
        self,
        content: str,
        user_id: str = "system",
        importance: float = 0.8,
        metadata: dict[str, str] | None = None,
    ) -> str:
        from common.utils import generate_id

        entry = MemoryEntry(
            memory_id=generate_id(),
            user_id=user_id,
            content=content,
            memory_type="semantic",
            importance=importance,
            metadata=metadata,
        )
        await self.semantic.save(entry)
        return entry.memory_id


_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager

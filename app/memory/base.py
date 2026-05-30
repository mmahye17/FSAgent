from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from models.memory import MemoryEntry, MemorySearchRequest, MemorySearchResult


class MemoryStore(ABC):
    store_type: str = "base"

    @abstractmethod
    async def save(self, entry: MemoryEntry) -> None:
        ...

    @abstractmethod
    async def get(self, memory_id: str) -> MemoryEntry | None:
        ...

    @abstractmethod
    async def search(self, request: MemorySearchRequest) -> list[MemorySearchResult]:
        ...

    @abstractmethod
    async def delete(self, memory_id: str) -> None:
        ...

    @abstractmethod
    async def clear_session(self, session_id: str) -> None:
        ...

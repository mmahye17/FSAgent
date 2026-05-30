from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, text

from app.memory.base import MemoryStore
from common.logger import get_logger
from common.utils import utc_now
from db.models.episodic_memory import EpisodicMemoryModel
from db.session import async_session_factory
from models.memory import MemoryEntry, MemorySearchRequest, MemorySearchResult

logger = get_logger(__name__)

RETENTION_DAYS = 90


class EpisodicMemoryStore(MemoryStore):
    store_type = "episodic"

    async def save(self, entry: MemoryEntry) -> None:
        async with async_session_factory() as session:
            record = EpisodicMemoryModel(
                memory_id=entry.memory_id,
                session_id=entry.session_id,
                user_id=entry.user_id,
                content=entry.content,
                importance=entry.importance,
                memory_metadata=entry.metadata,
                expires_at=utc_now() + timedelta(days=RETENTION_DAYS),
            )
            session.add(record)
            await session.commit()

    async def get(self, memory_id: str) -> MemoryEntry | None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(EpisodicMemoryModel).where(
                    EpisodicMemoryModel.memory_id == memory_id
                )
            )
            record = result.scalar_one_or_none()
            if not record:
                return None
            return MemoryEntry(
                memory_id=record.memory_id,
                session_id=record.session_id,
                user_id=record.user_id,
                content=record.content,
                importance=record.importance,
                metadata=record.memory_metadata,
                created_at=record.created_at,
            )

    async def search(self, request: MemorySearchRequest) -> list[MemorySearchResult]:
        async with async_session_factory() as session:
            query = (
                select(EpisodicMemoryModel)
                .where(EpisodicMemoryModel.content.ilike(f"%{request.query}%"))
                .order_by(EpisodicMemoryModel.created_at.desc())
                .limit(request.top_k)
            )
            if request.user_id:
                query = query.where(EpisodicMemoryModel.user_id == request.user_id)

            result = await session.execute(query)
            records = result.scalars().all()

            return [
                MemorySearchResult(
                    memory_id=r.memory_id,
                    content=r.content,
                    score=r.importance,
                    memory_type="episodic",
                    metadata=r.memory_metadata,
                    created_at=r.created_at,
                )
                for r in records
            ]

    async def get_user_history(
        self, user_id: str, days: int = 30, limit: int = 50
    ) -> list[MemoryEntry]:
        async with async_session_factory() as session:
            since = utc_now() - timedelta(days=days)
            result = await session.execute(
                select(EpisodicMemoryModel)
                .where(EpisodicMemoryModel.user_id == user_id)
                .where(EpisodicMemoryModel.created_at >= since)
                .order_by(EpisodicMemoryModel.created_at.desc())
                .limit(limit)
            )
            records = result.scalars().all()
            return [
                MemoryEntry(
                    memory_id=r.memory_id,
                    session_id=r.session_id,
                    user_id=r.user_id,
                    content=r.content,
                    importance=r.importance,
                    metadata=r.memory_metadata,
                    created_at=r.created_at,
                )
                for r in records
            ]

    async def delete(self, memory_id: str) -> None:
        async with async_session_factory() as session:
            result = await session.execute(
                select(EpisodicMemoryModel).where(
                    EpisodicMemoryModel.memory_id == memory_id
                )
            )
            record = result.scalar_one_or_none()
            if record:
                await session.delete(record)
                await session.commit()

    async def clear_session(self, session_id: str) -> None:
        async with async_session_factory() as session:
            await session.execute(
                text(
                    f"DELETE FROM episodic_memories WHERE session_id = '{session_id}'"
                )
            )
            await session.commit()

    async def cleanup_expired(self) -> int:
        async with async_session_factory() as session:
            result = await session.execute(
                text(
                    "DELETE FROM episodic_memories WHERE expires_at < NOW()"
                )
            )
            await session.commit()
            return result.rowcount or 0


_episodic_store: EpisodicMemoryStore | None = None


def get_episodic_memory() -> EpisodicMemoryStore:
    global _episodic_store
    if _episodic_store is None:
        _episodic_store = EpisodicMemoryStore()
    return _episodic_store

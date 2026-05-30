from __future__ import annotations

from typing import Any

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections
from pymilvus.exceptions import MilvusException

from app.config import get_settings
from app.memory.base import MemoryStore
from common.embedding import get_embedding_client
from common.logger import get_logger
from common.utils import generate_id, utc_now
from models.memory import MemoryEntry, MemorySearchRequest, MemorySearchResult

logger = get_logger(__name__)


class SemanticMemoryStore(MemoryStore):
    store_type = "semantic"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._collection: Collection | None = None
        self._initialized = False

    async def _ensure_collection(self) -> Collection:
        if self._collection is not None:
            return self._collection

        connections.connect(
            alias="default",
            host=self.settings.MILVUS_HOST,
            port=self.settings.MILVUS_PORT,
        )

        collection_name = self.settings.MILVUS_COLLECTION_NAME

        try:
            self._collection = Collection(collection_name)
        except MilvusException:
            self._collection = await self._create_collection(collection_name)

        self._collection.load()
        return self._collection

    async def _create_collection(self, name: str) -> Collection:
        dim = self.settings.EMBEDDING_DIMENSION

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="memory_id", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="metadata_json", dtype=DataType.VARCHAR, max_length=4096),
        ]
        schema = CollectionSchema(fields, description="FSAgent Semantic Memory")
        collection = Collection(name, schema=schema)

        index_params = {
            "metric_type": "IP",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
        collection.create_index("embedding", index_params)
        return collection

    async def save(self, entry: MemoryEntry) -> None:
        collection = await self._ensure_collection()
        emb_client = get_embedding_client()

        if entry.embedding is None:
            entry.embedding = await emb_client.embed_single(entry.content)

        import json

        data = [
            [entry.memory_id],
            [entry.user_id],
            [entry.content],
            [entry.embedding],
            [json.dumps(entry.metadata or {})],
        ]
        collection.insert(data)
        logger.debug("semantic_memory_saved", memory_id=entry.memory_id)

    async def get(self, memory_id: str) -> MemoryEntry | None:
        collection = await self._ensure_collection()
        results = collection.query(
            expr=f'memory_id == "{memory_id}"',
            output_fields=["memory_id", "user_id", "content", "metadata_json"],
        )
        if not results:
            return None
        r = results[0]
        import json

        return MemoryEntry(
            memory_id=r["memory_id"],
            user_id=r["user_id"],
            content=r["content"],
            memory_type="semantic",
            metadata=json.loads(r.get("metadata_json", "{}")),
        )

    async def search(self, request: MemorySearchRequest) -> list[MemorySearchResult]:
        collection = await self._ensure_collection()
        emb_client = get_embedding_client()

        query_embedding = await emb_client.embed_single(request.query)

        expr_parts = []
        if request.user_id:
            expr_parts.append(f'user_id == "{request.user_id}"')
        expr = " && ".join(expr_parts) if expr_parts else None

        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": 10}},
            limit=request.top_k,
            expr=expr,
            output_fields=["memory_id", "content", "metadata_json"],
        )

        import json

        search_results = []
        for hits in results:
            for hit in hits:
                if hit.score >= request.min_score:
                    search_results.append(
                        MemorySearchResult(
                            memory_id=hit.entity.get("memory_id", ""),
                            content=hit.entity.get("content", ""),
                            score=float(hit.score),
                            memory_type="semantic",
                            metadata=json.loads(
                                hit.entity.get("metadata_json", "{}")
                            ),
                        )
                    )

        return search_results

    async def delete(self, memory_id: str) -> None:
        collection = await self._ensure_collection()
        collection.delete(f'memory_id == "{memory_id}"')

    async def clear_session(self, session_id: str) -> None:
        pass


_semantic_store: SemanticMemoryStore | None = None


def get_semantic_memory() -> SemanticMemoryStore:
    global _semantic_store
    if _semantic_store is None:
        _semantic_store = SemanticMemoryStore()
    return _semantic_store

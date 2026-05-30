from __future__ import annotations

from openai import AsyncOpenAI

from app.config import Settings, get_settings
from common.logger import get_logger

logger = get_logger(__name__)


class EmbeddingClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client = AsyncOpenAI(
            api_key=self.settings.EMBEDDING_API_KEY,
            base_url=self.settings.EMBEDDING_BASE_URL,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self.settings.EMBEDDING_MODEL,
            input=texts,
        )
        return [d.embedding for d in response.data]

    async def embed_single(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]


_embedding_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client

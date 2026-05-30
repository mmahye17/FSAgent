from __future__ import annotations

from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from app.config import Settings, get_settings
from common.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client = AsyncOpenAI(
            api_key=self.settings.LLM_API_KEY,
            base_url=self.settings.LLM_BASE_URL,
        )

    #llm调用得到response转json
    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        response = await self._client.chat.completions.create(
            model=model or self.settings.LLM_MODEL,
            messages=messages,
            max_tokens=max_tokens or self.settings.LLM_MAX_TOKENS,
            temperature=temperature or self.settings.LLM_TEMPERATURE,
            tools=tools,
            tool_choice=tool_choice if tools else None,
        )
        return response.model_dump()

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=model or self.settings.LLM_MODEL,
            messages=messages,
            max_tokens=max_tokens or self.settings.LLM_MAX_TOKENS,
            temperature=temperature or self.settings.LLM_TEMPERATURE,
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


    # 简单的llm对话，simple_prompt调用得到大模型json回复然后输出内容
    async def simple_prompt(
        self,
        system: str,
        user: str,
        *,
        model: str | None = None,
    ) -> str:
        response = await self.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            model=model,
        )
        return response["choices"][0]["message"]["content"] or ""


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

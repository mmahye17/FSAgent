from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === 应用 ===
    APP_NAME: str = "FSAgent"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # === 服务 ===
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # === PostgreSQL ===
    DATABASE_URL: str = "postgresql+asyncpg://fsagent:fsagent@localhost:5432/agentdb"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # === Redis ===
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""

    # === Redis Cluster (Wiki Cache) ===
    REDIS_CLUSTER_NODES: str = ""
    REDIS_CLUSTER_PASSWORD: str = ""

    # === Milvus ===
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "fsagent_semantic_memory"

    # === LLM ===
    LLM_PROVIDER: Literal["openai", "anthropic", "deepseek"] = "openai"
    LLM_MODEL: str = "gpt-4o"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.7

    # === Embedding ===
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_DIMENSION: int = 1536

    # === 飞书 ===
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_VERIFICATION_TOKEN: str = ""
    FEISHU_ENCRYPT_KEY: str = ""
    FEISHU_BOT_NAME: str = "FSAgent"

    # === 企业微信 ===
    WECHAT_CORP_ID: str = ""
    WECHAT_CORP_SECRET: str = ""
    WECHAT_AGENT_ID: str = ""
    WECHAT_TOKEN: str = ""
    WECHAT_ENCODING_AES_KEY: str = ""

    # === JWT ===
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    API_KEY_HEADER: str = "X-API-Key"

    # === 限流 ===
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_WEBHOOK: str = "120/minute"

    # === Wiki Cache ===
    WIKI_CACHE_TTL: int = 3600
    WIKI_REFRESH_INTERVAL: int = 300

    # === 会话 ===
    SESSION_TTL_SECONDS: int = 1800
    SESSION_MAX_MESSAGES: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()

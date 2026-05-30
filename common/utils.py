from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime


def generate_id() -> str:
    return uuid.uuid4().hex[:16]


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def truncate_text(text: str, max_length: int = 2000) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."

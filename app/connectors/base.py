from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IMUser:
    user_id: str
    display_name: str = ""
    avatar_url: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IMMessage:
    message_id: str
    content: str
    sender: IMUser
    group_id: str = ""
    chat_type: str = "group"
    mentioned_bot: bool = False
    reply_to: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class IMGroup:
    group_id: str
    name: str = ""
    member_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class IMConnector(ABC):
    platform: str = "unknown"

    @abstractmethod
    async def verify_signature(self, data: dict[str, Any], headers: dict[str, str]) -> bool:
        ...

    @abstractmethod
    async def parse_message(self, raw_data: dict[str, Any]) -> IMMessage:
        ...

    @abstractmethod
    async def send_message(
        self, to: str, content: str, *, msg_type: str = "text", **kwargs: Any
    ) -> str:
        ...

    @abstractmethod
    async def get_user_info(self, user_id: str) -> IMUser:
        ...

    @abstractmethod
    async def get_group_info(self, group_id: str) -> IMGroup:
        ...

    @abstractmethod
    async def create_group(
        self, name: str, member_ids: list[str]
    ) -> IMGroup:
        ...

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings
from common.http import async_get, async_post
from common.logger import get_logger

logger = get_logger(__name__)


class FeishuClient:
    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    async def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        resp = await async_post(
            url,
            json={
                "app_id": self.settings.FEISHU_APP_ID,
                "app_secret": self.settings.FEISHU_APP_SECRET,
            },
        )
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Failed to get tenant access token: {data}")

        self._access_token = data["tenant_access_token"]
        self._token_expires_at = time.time() + data.get("expire", 7200)
        return self._access_token

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> dict[str, Any]:
        token = await self._get_access_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.request(
                method, f"{self.BASE_URL}{path}", headers=headers, **kwargs
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.error("feishu_api_error", path=path, code=data.get("code"), msg=data.get("msg"))
            return data

    async def get(self, path: str, **params: Any) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, **body: Any) -> dict[str, Any]:
        return await self._request("POST", path, json=body)

    # === 用户 ===
    async def get_user(self, user_id: str) -> dict[str, Any]:
        resp = await self.get(f"/contact/v3/users/{user_id}")
        return resp.get("data", {}).get("user", {})

    # === 消息 ===
    async def send_message(
        self,
        receive_id: str,
        content: str,
        msg_type: str = "text",
    ) -> dict[str, Any]:
        body = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content,
        }
        return await self.post("/im/v1/messages", params={"receive_id_type": "chat_id"}, **body)

    # === 群组 ===
    async def create_group(
        self, name: str, user_ids: list[str]
    ) -> dict[str, Any]:
        return await self.post(
            "/im/v1/chats",
            name=name,
            user_id_list=user_ids,
            chat_type="group",
        )

    async def get_group(self, chat_id: str) -> dict[str, Any]:
        resp = await self.get(f"/im/v1/chats/{chat_id}")
        return resp.get("data", {})

    # === 日历 ===
    async def get_freebusy(
        self, user_ids: list[str], start_time: str, end_time: str
    ) -> dict[str, Any]:
        return await self.post(
            "/calendar/v4/freebusy/list",
            user_id=user_ids,
            start_time=start_time,
            end_time=end_time,
        )

    async def create_calendar_event(
        self, calendar_id: str, event: dict[str, Any]
    ) -> dict[str, Any]:
        resp = await self.post(f"/calendar/v4/calendars/{calendar_id}/events", **event)
        return resp.get("data", {}).get("event", {})

    # === 文档 ===
    async def get_doc_content(self, doc_token: str) -> dict[str, Any]:
        resp = await self.get(f"/docx/v1/documents/{doc_token}/raw_content")
        return resp.get("data", {})

    # === 妙记 ===
    async def get_minutes_transcript(self, minutes_token: str) -> dict[str, Any]:
        resp = await self.get(f"/vc/v1/meetings/{minutes_token}/transcript")
        return resp.get("data", {})


_feishu_client: FeishuClient | None = None


def get_feishu_client() -> FeishuClient:
    global _feishu_client
    if _feishu_client is None:
        _feishu_client = FeishuClient()
    return _feishu_client

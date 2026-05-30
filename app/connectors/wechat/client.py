from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import get_settings
from common.http import async_get, async_post
from common.logger import get_logger

logger = get_logger(__name__)


class WechatClient:
    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    async def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        url = f"{self.BASE_URL}/gettoken"
        resp = await async_get(
            url,
            params={
                "corpid": self.settings.WECHAT_CORP_ID,
                "corpsecret": self.settings.WECHAT_CORP_SECRET,
            },
        )
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"Failed to get access token: {data}")

        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 7200)
        return self._access_token

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> dict[str, Any]:
        token = await self._get_access_token()
        params = kwargs.pop("params", {})
        params["access_token"] = token

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.request(
                method, f"{self.BASE_URL}{path}", params=params, **kwargs
            )
            data = resp.json()
            if data.get("errcode") != 0:
                logger.error(
                    "wechat_api_error", path=path, errcode=data.get("errcode")
                )
            return data

    async def get(self, path: str, **params: Any) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, **body: Any) -> dict[str, Any]:
        return await self._request("POST", path, json=body)

    # === 消息 ===
    async def send_message(
        self,
        to_user: str = "",
        to_party: str = "",
        to_tag: str = "",
        content: str = "",
        msg_type: str = "text",
        safe: int = 0,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "msgtype": msg_type,
            "agentid": int(self.settings.WECHAT_AGENT_ID),
            "safe": safe,
        }
        if msg_type == "text":
            body["text"] = {"content": content}
        elif msg_type == "markdown":
            body["markdown"] = {"content": content}

        if to_user:
            body["touser"] = to_user
        if to_party:
            body["toparty"] = to_party
        if to_tag:
            body["totag"] = to_tag

        return await self.post("/message/send", **body)

    # === 用户 ===
    async def get_user(self, user_id: str) -> dict[str, Any]:
        resp = await self.get("/user/get", userid=user_id)
        return resp

    # === 部门 ===
    async def get_department_list(self, dept_id: int = 1) -> dict[str, Any]:
        resp = await self.get("/department/list", id=dept_id)
        return resp

    # === 群聊 ===
    async def create_group_chat(
        self, name: str, user_ids: list[str]
    ) -> dict[str, Any]:
        return await self.post("/appchat/create", name=name, userlist=user_ids)

    async def send_group_message(
        self, chat_id: str, content: str, msg_type: str = "text"
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "chatid": chat_id,
            "msgtype": msg_type,
        }
        if msg_type == "text":
            body["text"] = {"content": content}
        elif msg_type == "markdown":
            body["markdown"] = {"content": content}
        return await self.post("/appchat/send", **body)


_wechat_client: WechatClient | None = None


def get_wechat_client() -> WechatClient:
    global _wechat_client
    if _wechat_client is None:
        _wechat_client = WechatClient()
    return _wechat_client

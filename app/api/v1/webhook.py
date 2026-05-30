from __future__ import annotations

import json

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from common.logger import get_logger

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = get_logger(__name__)


class WebhookResponse(BaseModel):
    code: int = 0
    message: str = "ok"


# === 飞书 ===

@router.post("/feishu")
async def feishu_webhook(request: Request) -> WebhookResponse:
    body = await request.body()
    data = json.loads(body) if body else {}
    logger.debug("飞书消息为", data=data)
    logger.info("收到飞书的消息！！", event_type=data.get("header", {}).get("event_type"))

    from app.connectors.feishu.event_handler import FeishuEventHandler

    handler = FeishuEventHandler()
    await handler.handle(data)

    return WebhookResponse()


@router.get("/feishu")
async def feishu_url_verify(
    challenge: str = "",
    token: str = "",
    type_str: str = "",
) -> dict:
    if type_str == "url_verification":
        return {"challenge": challenge}
    raise HTTPException(status_code=400, detail="Invalid verification request")


# === 企业微信 ===

@router.post("/wechat")
async def wechat_webhook(request: Request) -> WebhookResponse:
    body = await request.body()
    data = json.loads(body) if body else {}
    logger.info("wechat_webhook_received", msg_type=data.get("MsgType"))

    from app.connectors.wechat.event_handler import WechatEventHandler

    handler = WechatEventHandler()
    await handler.handle(data)

    return WebhookResponse()


@router.get("/wechat")
async def wechat_url_verify(
    msg_signature: str = "",
    timestamp: str = "",
    nonce: str = "",
    echostr: str = "",
) -> str:
    return echostr

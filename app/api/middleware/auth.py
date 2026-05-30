from __future__ import annotations

from fastapi import Header, HTTPException, Request

from app.config import get_settings


async def verify_api_key(request: Request, x_api_key: str = Header(default="")) -> None:
    settings = get_settings()
    if not settings.API_KEY_HEADER:
        return
    expected = settings.JWT_SECRET_KEY
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")


async def verify_bearer_token(request: Request, authorization: str = Header(default="")) -> dict:
    import jwt

    settings = get_settings()
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

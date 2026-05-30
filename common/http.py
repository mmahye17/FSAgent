from __future__ import annotations

from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from common.errors import ExternalServiceError
from common.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
DEFAULT_MAX_RETRIES = 3


@retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def async_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout or DEFAULT_TIMEOUT) as client:
        logger.debug("HTTP request", method=method, url=url)
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            params=params,
        )
        if response.status_code >= 500:
            raise ExternalServiceError(
                f"HTTP {method} {url} failed: {response.status_code}"
            )
        return response


async def async_get(url: str, **kwargs: Any) -> httpx.Response:
    return await async_request("GET", url, **kwargs)


async def async_post(url: str, **kwargs: Any) -> httpx.Response:
    return await async_request("POST", url, **kwargs)


async def async_put(url: str, **kwargs: Any) -> httpx.Response:
    return await async_request("PUT", url, **kwargs)


async def async_delete(url: str, **kwargs: Any) -> httpx.Response:
    return await async_request("DELETE", url, **kwargs)

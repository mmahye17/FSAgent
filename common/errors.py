from __future__ import annotations

from typing import Any


class FSAgentError(Exception):
    def __init__(self, message: str, code: int = 500, detail: Any = None):
        self.message = message
        self.code = code
        self.detail = detail
        super().__init__(message)


# === 认证 ===
class AuthenticationError(FSAgentError):
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, code=401)


class PermissionDeniedError(FSAgentError):
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, code=403)


# === 资源 ===
class NotFoundError(FSAgentError):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, code=404)


class ConflictError(FSAgentError):
    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, code=409)


# === 业务 ===
class SkillExecutionError(FSAgentError):
    def __init__(self, message: str = "技能执行失败", detail: Any = None):
        super().__init__(message, code=500, detail=detail)


class PlanFailedError(FSAgentError):
    def __init__(self, message: str = "计划执行失败", detail: Any = None):
        super().__init__(message, code=500, detail=detail)


class IntentNotRecognizedError(FSAgentError):
    def __init__(self, message: str = "无法识别意图"):
        super().__init__(message, code=422)


# === 限流 ===
class RateLimitExceededError(FSAgentError):
    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(message, code=429)


# === 外部服务 ===
class ExternalServiceError(FSAgentError):
    def __init__(self, message: str = "外部服务调用失败", detail: Any = None):
        super().__init__(message, code=502, detail=detail)


class FeishuAPIError(ExternalServiceError):
    def __init__(self, message: str = "飞书 API 调用失败", detail: Any = None):
        super().__init__(message, detail=detail)

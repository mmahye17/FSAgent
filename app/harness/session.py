from __future__ import annotations

from datetime import datetime

from common.utils import generate_id, utc_now


class Session:
    def __init__(
        self,
        session_id: str | None = None,
        user_id: str = "",
        platform: str = "api",
        group_id: str | None = None,
    ):
        self.session_id = session_id or generate_id()
        self.user_id = user_id
        self.platform = platform
        self.group_id = group_id
        self.status = "active"
        self.messages: list[dict] = []
        self.metadata: dict[str, str] = {}
        self.created_at: datetime = utc_now()
        self.updated_at: datetime = utc_now()

    def add_message(self, role: str, content: str, **kwargs: str) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": utc_now().isoformat(),
            **kwargs,
        })
        self.updated_at = utc_now()

    @property
    def history(self) -> list[dict[str, str]]:
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    def close(self) -> None:
        self.status = "closed"
        self.updated_at = utc_now()


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create(
        self,
        session_id: str,
        user_id: str = "",
        platform: str = "api",
        group_id: str | None = None,
    ) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(
                session_id=session_id,
                user_id=user_id,
                platform=platform,
                group_id=group_id,
            )
        return self._sessions[session_id]

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    @property
    def active_count(self) -> int:
        return sum(1 for s in self._sessions.values() if s.is_active)


_session_store = SessionStore()


def get_session_store() -> SessionStore:
    return _session_store

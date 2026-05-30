from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

from common.utils import generate_id


def _default_id() -> str:
    return generate_id()


class Base(DeclarativeBase):
    pass

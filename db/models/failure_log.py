from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class FailureLogModel(Base):
    __tablename__ = "failure_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    log_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    error_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolved: Mapped[bool] = mapped_column(default=False)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import IO

import structlog

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    """去掉 ANSI 颜色码"""
    return _ANSI_RE.sub("", text)


class TeeWriter:
    """同时写终端（带颜色）和日志文件（纯文本）"""

    def __init__(self, log_dir: Path = LOG_DIR, backup_count: int = 90):
        self._log_dir = log_dir
        self._backup_count = backup_count
        self._current_date: str = ""
        self._file: IO[str] | None = None

    def write(self, s: str) -> int:
        # 终端保留颜色
        n = sys.stderr.write(s)

        # 文件去掉 ANSI 码
        self._ensure_file()
        if self._file:
            self._file.write(_strip_ansi(s))
            self._file.flush()

        return n

    def flush(self) -> None:
        sys.stderr.flush()
        if self._file:
            self._file.flush()

    def _ensure_file(self) -> None:
        self._log_dir.mkdir(exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._current_date:
            if self._file:
                self._file.close()
            self._current_date = today
            path = self._log_dir / f"{today}.log"
            self._file = open(path, "a", encoding="utf-8")
            self._cleanup()

    def _cleanup(self) -> None:
        files = sorted(self._log_dir.glob("*.log"))
        while len(files) > self._backup_count:
            files[0].unlink()
            files.pop(0)

    def close(self) -> None:
        if self._file:
            self._file.close()
            self._file = None

    def __del__(self) -> None:
        self.close()


def setup_logging(log_level: str = "INFO", *, json_format: bool = False) -> None:
    LOG_DIR.mkdir(exist_ok=True)

    writer = TeeWriter()

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    # 终端用可读格式，文件始终用 JSON
    renderer = (
        structlog.processors.JSONRenderer()
        if json_format
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.contextvars.merge_contextvars,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            timestamper,
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=writer),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name or __name__)

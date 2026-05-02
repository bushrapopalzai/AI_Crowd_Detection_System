"""Centralised logging configuration."""

import logging
import logging.handlers
from pathlib import Path
from config import get


def setup() -> None:
    level_name: str = get("logging", "level", "INFO")
    log_file: str = get("logging", "file", "detection.log")
    max_bytes: int = get("logging", "max_bytes", 10_485_760)
    backup_count: int = get("logging", "backup_count", 3)

    level = getattr(logging, level_name.upper(), logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)

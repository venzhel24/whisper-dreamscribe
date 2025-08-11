"""Настройка логирования с помощью loguru."""

import sys
from pathlib import Path
from loguru import logger

from ..config import settings


def setup_logger() -> None:
    """Настраивает логирование."""
    # Удаляем стандартный handler
    logger.remove()

    # Консольный вывод
    logger.add(
        sys.stdout,
        format=settings.log_format,
        level=settings.log_level,
        colorize=True,
    )

    # Файловый лог
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "whisper-worker.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        )

    logger.info("Логирование настроено")

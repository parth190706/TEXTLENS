"""
TextLens — Structured logging using Loguru.
"""
import sys
from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    logger.remove()
    level = "DEBUG" if settings.APP_DEBUG else "INFO"
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
    )
    logger.add(
        "logs/textlens.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time} | {level} | {name}:{function}:{line} — {message}",
    )

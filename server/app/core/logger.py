"""
Logger Configuration
Structured logging setup for production
"""

import logging
import sys
from typing import Optional

from loguru import logger as loguru_logger


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = "logs/jarvis.log",
) -> None:
    """
    Configure logging with loguru

    Args:
        level: Logging level
        log_file: Optional log file path
    """
    # Remove default handler
    loguru_logger.remove()

    # Console handler
    loguru_logger.add(
        sys.stderr,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )

    # File handler
    if log_file:
        loguru_logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation="500 MB",
            retention="10 days",
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

"""
Structured Logging Setup
JSON logging with file rotation and console output
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
import sys

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    Converts log records to JSON for better parsing and analysis
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability
    """

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[41m",   # Red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors"""
        color = self.COLORS.get(record.levelname, self.RESET)
        formatted = (
            f"{color}[{record.levelname:8}]{self.RESET} "
            f"{record.name:30} | "
            f"{record.getMessage()}"
        )

        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def setup_logging() -> None:
    """
    Configure logging for the application
    Sets up:
    - Console handler (colored text)
    - File handler (JSON format)
    """

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Remove existing handlers
    root_logger.handlers = []

    # ========================================================================
    # Console Handler (colored output)
    # ========================================================================

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)

    # ========================================================================
    # File Handler (JSON format)
    # ========================================================================

    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setLevel(logging.DEBUG)  # Always log debug to file
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # ========================================================================
    # Suppress noisy loggers
    # ========================================================================

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.INFO)

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Logging configured - Level: {settings.LOG_LEVEL}, Environment: {settings.ENVIRONMENT}")


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance
    """
    return logging.getLogger(name)

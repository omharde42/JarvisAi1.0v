"""
Structured Logging Configuration
JSON logging with file rotation and console output
"""

import logging
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    Converts log records to JSON format for better parsing and analysis
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
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
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Simple text formatter for console output"""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[41m",   # Red background
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.RESET)
        
        formatted = (
            f"{color}[{record.levelname:8}]{self.RESET} "
            f"{record.name:20} | "
            f"{record.funcName:15} | "
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
    - File handler (JSON format with rotation)
    - Root logger
    """
    
    # Create logs directory
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # ========================================================================
    # Console Handler (colored output)
    # ========================================================================
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_handler.setFormatter(TextFormatter())
    root_logger.addHandler(console_handler)
    
    # ========================================================================
    # File Handler (JSON format with rotation)
    # ========================================================================
    
    file_handler = RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE_MB * 1024 * 1024,
        backupCount=settings.LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(logging.DEBUG)  # Always log debug to file
    
    if settings.LOG_FORMAT.lower() == "json":
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(TextFormatter())
    
    root_logger.addHandler(file_handler)
    
    # ========================================================================
    # Suppress noisy loggers
    # ========================================================================
    
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Logging configured - Level: {settings.LOG_LEVEL}, Format: {settings.LOG_FORMAT}")


# ============================================================================
# Context Manager for Request-level Logging
# ============================================================================

class RequestLogger:
    """Context manager for logging request context"""
    
    def __init__(self, logger: logging.Logger, user_id: str = None, request_id: str = None):
        self.logger = logger
        self.user_id = user_id
        self.request_id = request_id
    
    def __enter__(self):
        """Enter context"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        if exc_type is not None:
            self.logger.error(f"Exception in request: {exc_val}", exc_info=(exc_type, exc_val, exc_tb))
    
    def info(self, message: str, **kwargs):
        """Log info with context"""
        extra = {
            "user_id": self.user_id,
            "request_id": self.request_id,
            "extra_data": kwargs,
        }
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error with context"""
        extra = {
            "user_id": self.user_id,
            "request_id": self.request_id,
            "extra_data": kwargs,
        }
        self.logger.error(message, extra=extra)

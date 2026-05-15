"""
Custom Exception Classes
Centralized exception handling for the application
"""

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class JarvisException(Exception):
    """
    Base exception for all Jarvis-related errors
    Provides structured error information
    """

    def __init__(
        self,
        message: str,
        error_code: str = "JARVIS_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class LLMError(JarvisException):
    """LLM provider error"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="LLM_ERROR",
            status_code=503,
            details=details,
        )


class ToolExecutionError(JarvisException):
    """Tool execution error"""

    def __init__(self, tool_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {message}",
            error_code="TOOL_EXECUTION_ERROR",
            status_code=400,
            details={"tool": tool_name, **(details or {})},
        )


class MemoryError(JarvisException):
    """Memory system error"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="MEMORY_ERROR",
            status_code=500,
            details=details,
        )


class PlanningError(JarvisException):
    """Task planning error"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PLANNING_ERROR",
            status_code=400,
            details=details,
        )


class AuthenticationError(JarvisException):
    """Authentication error"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            status_code=401,
        )


class ValidationError(JarvisException):
    """Validation error"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field} if field else {},
        )


class RateLimitError(JarvisException):
    """Rate limit exceeded"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details={"retry_after": retry_after},
        )


class TimeoutError(JarvisException):
    """Request timeout error"""

    def __init__(self, message: str, timeout_seconds: int = 30):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            status_code=504,
            details={"timeout_seconds": timeout_seconds},
        )

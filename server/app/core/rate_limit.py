"""
Rate Limiting Middleware
Prevents abuse with request rate limiting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter
    Tracks requests per client/endpoint
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
    ):
        """
        Initialize rate limiter

        Args:
            max_requests: Max requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        logger.info(
            f"✅ Rate Limiter initialized "
            f"({max_requests} requests per {window_seconds}s)"
        )

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed for client

        Args:
            client_id: Client identifier (IP, user ID, etc)

        Returns:
            True if request is allowed
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Clean old requests
        self.requests[client_id] = [
            req_time
            for req_time in self.requests[client_id]
            if req_time > window_start
        ]

        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_id}")
            return False

        # Record request
        self.requests[client_id].append(now)
        return True

    def get_remaining(self, client_id: str) -> int:
        """
        Get remaining requests for client

        Args:
            client_id: Client identifier

        Returns:
            Number of remaining requests
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        self.requests[client_id] = [
            req_time
            for req_time in self.requests[client_id]
            if req_time > window_start
        ]

        return max(0, self.max_requests - len(self.requests[client_id]))

    def cleanup(self) -> None:
        """Clean up old request records"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                req_time
                for req_time in self.requests[client_id]
                if req_time > window_start
            ]

            if not self.requests[client_id]:
                del self.requests[client_id]

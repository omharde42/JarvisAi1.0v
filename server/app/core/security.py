"""
Security Module
API key protection, JWT auth, and request validation
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Centralized security management
    Handles authentication, API keys, and rate limiting
    """

    def __init__(self):
        """Initialize security manager"""
        self.rate_limits: Dict[str, list] = {}
        self.rate_limit_window = 60  # seconds
        self.rate_limit_max = 100  # requests per window

    def hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key for storage
        Uses SHA256 with salt
        """
        salt = secrets.token_hex(16)
        key_hash = hashlib.pbkdf2_hmac(
            "sha256",
            api_key.encode(),
            salt.encode(),
            100000,
        )
        return f"{salt}${key_hash.hex()}"

    def verify_api_key(self, api_key: str, api_key_hash: str) -> bool:
        """
        Verify an API key against its hash
        """
        try:
            salt, key_hash = api_key_hash.split("$")
            test_hash = hashlib.pbkdf2_hmac(
                "sha256",
                api_key.encode(),
                salt.encode(),
                100000,
            ).hex()
            return secrets.compare_digest(test_hash, key_hash)
        except Exception as e:
            logger.error(f"API key verification failed: {str(e)}")
            return False

    def generate_api_key(self, user_id: str) -> str:
        """
        Generate a secure API key for a user
        Format: jar_<random_64_chars>
        """
        random_part = secrets.token_urlsafe(48)
        return f"jar_{random_part}"

    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limit
        Returns True if allowed, False if rate limited
        """
        now = datetime.utcnow()

        # Initialize or clean old entries
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []

        # Remove old timestamps outside window
        self.rate_limits[identifier] = [
            ts
            for ts in self.rate_limits[identifier]
            if (now - ts).total_seconds() < self.rate_limit_window
        ]

        # Check if limit exceeded
        if len(self.rate_limits[identifier]) >= self.rate_limit_max:
            return False

        # Add current request timestamp
        self.rate_limits[identifier].append(now)
        return True

    def get_rate_limit_status(self, identifier: str) -> Dict[str, int]:
        """
        Get rate limit status for an identifier
        """
        now = datetime.utcnow()

        if identifier not in self.rate_limits:
            return {"requests": 0, "limit": self.rate_limit_max}

        # Count requests in window
        requests = len(
            [
                ts
                for ts in self.rate_limits[identifier]
                if (now - ts).total_seconds() < self.rate_limit_window
            ]
        )

        return {"requests": requests, "limit": self.rate_limit_max}


# Global security manager
security_manager = SecurityManager()

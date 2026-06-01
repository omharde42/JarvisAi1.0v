"""
Simple In-Memory Response Cache
TTL-based caching for LLM responses
"""

import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with expiration"""

    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl = ttl

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "ttl": self.ttl,
            "is_expired": self.is_expired(),
        }


class ResponseCache:
    """
    Simple in-memory response cache

    Features:
    - Key-value storage
    - TTL-based expiration
    - Size limits
    - Hit/miss tracking
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize cache

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0
        logger.info(f"✅ Response Cache initialized (max_size: {max_size}, ttl: {default_ttl}s)")

    @staticmethod
    def _make_key(prompt: str) -> str:
        """Generate cache key from prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            prompt: Prompt/query

        Returns:
            Cached value or None
        """
        key = self._make_key(prompt)

        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]

        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None

        self.hits += 1
        logger.debug(f"✅ Cache hit for: {prompt[:50]}...")
        return entry.value

    def set(self, prompt: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache

        Args:
            prompt: Prompt/query
            value: Value to cache
            ttl: Optional TTL override
        """
        key = self._make_key(prompt)
        ttl = ttl or self.default_ttl

        # Enforce size limit (simple FIFO eviction)
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
            del self.cache[oldest_key]
            logger.debug(f"Cache evicted old entry: {oldest_key}")

        self.cache[key] = CacheEntry(value, ttl)
        logger.debug(f"💾 Cache set for: {prompt[:50]}... (ttl: {ttl}s)")

    def clear(self) -> None:
        """Clear all cache entries"""
        count = len(self.cache)
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info(f"🗑️  Cache cleared ({count} entries)")

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total,
        }

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries

        Returns:
            Number of entries removed
        """
        original_size = len(self.cache)
        self.cache = {k: v for k, v in self.cache.items() if not v.is_expired()}
        removed = original_size - len(self.cache)
        if removed > 0:
            logger.info(f"🧹 Cache cleanup removed {removed} expired entries")
        return removed

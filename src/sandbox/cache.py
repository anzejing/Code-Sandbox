"""Execution result caching for Code-Sandbox."""

import hashlib
import time
from dataclasses import dataclass, field

from .types import ExecutionResult


@dataclass
class CacheEntry:
    """Cached execution result."""

    code_hash: str
    result: ExecutionResult
    created_at: float = field(default_factory=time.time)
    access_count: int = 0

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if cache entry has expired."""
        return (time.time() - self.created_at) > ttl_seconds


class ExecutionCache:
    """Cache for code execution results.

    Caches results based on code hash to avoid re-executing identical code.
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize execution cache.

        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cached results
        """
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _hash_code(self, code: str) -> str:
        """Generate hash for code string."""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    def get(self, code: str) -> ExecutionResult | None:
        """Get cached result for code.

        Args:
            code: Python code string

        Returns:
            Cached ExecutionResult if found and not expired, None otherwise
        """
        code_hash = self._hash_code(code)
        entry = self._cache.get(code_hash)

        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired(self._ttl_seconds):
            del self._cache[code_hash]
            self._misses += 1
            return None

        entry.access_count += 1
        self._hits += 1
        return entry.result

    def set(self, code: str, result: ExecutionResult) -> None:
        """Cache execution result.

        Args:
            code: Python code string
            result: Execution result to cache
        """
        # Only cache successful results
        if result.status.value != "success":
            return

        code_hash = self._hash_code(code)

        # Enforce max size
        if len(self._cache) >= self._max_size:
            self._evict_oldest()

        self._cache[code_hash] = CacheEntry(code_hash=code_hash, result=result)

    def _evict_oldest(self) -> None:
        """Remove oldest entry from cache."""
        if not self._cache:
            return
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]

    def clear(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "ttl_seconds": self._ttl_seconds,
        }


# Global cache instance
_execution_cache: ExecutionCache | None = None


def get_execution_cache() -> ExecutionCache:
    """Get or create execution cache singleton."""
    global _execution_cache
    if _execution_cache is None:
        _execution_cache = ExecutionCache()
    return _execution_cache

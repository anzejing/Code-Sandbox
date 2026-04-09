"""Tests for execution cache module."""

from src.sandbox.cache import ExecutionCache, get_execution_cache
from src.sandbox.types import ExecutionResult, ExecutionStatus


class TestExecutionCache:
    """Test execution cache functionality."""

    def test_cache_miss(self) -> None:
        """Test cache miss returns None."""
        cache = ExecutionCache()
        result = cache.get("nonexistent_code")
        assert result is None

    def test_cache_hit(self) -> None:
        """Test cache hit returns result."""
        cache = ExecutionCache()
        code = 'print("test")'

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="test\n",
            stderr="",
            returncode=0,
            execution_time_ms=1.0,
        )
        cache.set(code, result)

        cached = cache.get(code)
        assert cached is not None
        assert cached.stdout == "test\n"

    def test_only_cache_success(self) -> None:
        """Test that only successful results are cached."""
        cache = ExecutionCache()
        code = 'print("error")'

        error_result = ExecutionResult(
            status=ExecutionStatus.ERROR,
            stdout="",
            stderr="error",
            returncode=1,
            execution_time_ms=1.0,
        )
        cache.set(code, error_result)

        cached = cache.get(code)
        assert cached is None  # Error not cached

    def test_cache_ttl(self) -> None:
        """Test cache TTL expiration."""
        cache = ExecutionCache(ttl_seconds=0)  # Immediate expiry

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="",
            stderr="",
            returncode=0,
            execution_time_ms=1.0,
        )
        cache.set("code", result)

        import time

        time.sleep(0.01)  # Wait for expiry
        cached = cache.get("code")
        assert cached is None  # Expired

    def test_cache_max_size(self) -> None:
        """Test cache max size enforcement."""
        cache = ExecutionCache(max_size=5)

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="",
            stderr="",
            returncode=0,
            execution_time_ms=1.0,
        )

        # Add 10 items
        for i in range(10):
            cache.set(f"code_{i}", result)

        # Should only have 5 items
        assert len(cache._cache) == 5

    def test_cache_clear(self) -> None:
        """Test clearing cache."""
        cache = ExecutionCache()

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="",
            stderr="",
            returncode=0,
            execution_time_ms=1.0,
        )
        cache.set("code", result)

        cache.clear()
        assert len(cache._cache) == 0

    def test_cache_stats(self) -> None:
        """Test cache statistics."""
        cache = ExecutionCache()

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="",
            stderr="",
            returncode=0,
            execution_time_ms=1.0,
        )

        # Generate hits and misses
        cache.set("code1", result)
        cache.get("code1")  # Hit
        cache.get("code1")  # Hit
        cache.get("code2")  # Miss
        cache.get("code3")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 2  # code2 and code3
        assert stats["size"] == 1
        assert "hit_rate" in stats

    def test_cache_access_count(self) -> None:
        """Test that access count is tracked."""
        cache = ExecutionCache()

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="",
            stderr="",
            returncode=0,
            execution_time_ms=1.0,
        )
        cache.set("code", result)

        cache.get("code")
        cache.get("code")
        cache.get("code")

        entry = cache._cache.get(cache._hash_code("code"))
        assert entry is not None
        assert entry.access_count == 3

    def test_singleton(self) -> None:
        """Test get_execution_cache returns singleton."""
        cache1 = get_execution_cache()
        cache2 = get_execution_cache()
        assert cache1 is cache2

"""Performance benchmarks for Code-Sandbox."""

import time
from collections.abc import Callable

import pytest

from src.sandbox.cache import ExecutionCache
from src.sandbox.engine import ExecutionEngine
from src.sandbox.types import ExecutionStatus, SandboxConfig


class TestExecutionPerformance:
    """Benchmark execution engine performance."""

    @pytest.mark.asyncio
    async def test_simple_print_latency(self) -> None:
        """Test latency of simple print statement."""
        engine = ExecutionEngine(SandboxConfig(timeout_seconds=5))

        start = time.perf_counter()
        result = await engine.execute('print("hello")')
        elapsed = time.perf_counter() - start

        assert result.status == ExecutionStatus.SUCCESS
        # Should complete in under 100ms for simple code
        assert elapsed < 0.1, f"Simple print took {elapsed:.3f}s"

    @pytest.mark.asyncio
    async def test_math_operations_latency(self) -> None:
        """Test latency of math operations."""
        engine = ExecutionEngine(SandboxConfig(timeout_seconds=5))
        code = """
import math
result = sum(math.sqrt(i) for i in range(1000))
print(f"{result:.2f}")
"""

        start = time.perf_counter()
        result = await engine.execute(code)
        elapsed = time.perf_counter() - start

        assert result.status == ExecutionStatus.SUCCESS
        # Should complete in under 200ms
        assert elapsed < 0.2, f"Math operations took {elapsed:.3f}s"

    @pytest.mark.asyncio
    async def test_concurrent_executions(self) -> None:
        """Test concurrent code executions."""
        import asyncio

        engine = ExecutionEngine(SandboxConfig(timeout_seconds=5))

        async def run_code(code: str) -> float:
            start = time.perf_counter()
            await engine.execute(code)
            return time.perf_counter() - start

        # Run 5 executions concurrently
        codes = [f'print("task {i}")' for i in range(5)]
        start = time.perf_counter()
        await asyncio.gather(*[run_code(code) for code in codes])
        total_time = time.perf_counter() - start

        # Concurrent execution should be faster than sequential
        # Sequential would take ~5x single execution time
        assert total_time < 1.0, f"Concurrent execution took {total_time:.3f}s"


class TestCachePerformance:
    """Benchmark cache performance."""

    def test_cache_hit_latency(self) -> None:
        """Test latency of cache hit."""
        cache = ExecutionCache()
        code = 'print("cached")'

        # First execution (miss)
        from src.sandbox.types import ExecutionResult, ExecutionStatus

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="cached\n",
            stderr="",
            returncode=0,
            execution_time_ms=1.0,
        )
        cache.set(code, result)

        # Cache hit
        start = time.perf_counter()
        cached = cache.get(code)
        elapsed = time.perf_counter() - start

        assert cached is not None
        # Cache hit should be very fast (< 1ms)
        assert elapsed < 0.001, f"Cache hit took {elapsed:.6f}s"

    def test_cache_hash_performance(self) -> None:
        """Test performance of code hashing."""
        cache = ExecutionCache()
        code = "x = sum(range(1000))\nprint(x)" * 10  # Longer code

        start = time.perf_counter()
        for _ in range(1000):
            cache._hash_code(code)
        elapsed = time.perf_counter() - start

        # Should hash 1000 times in under 10ms
        assert elapsed < 0.01, f"Hashing took {elapsed:.3f}s"

    def test_cache_eviction_performance(self) -> None:
        """Test performance of cache eviction."""
        cache = ExecutionCache(max_size=100)

        from src.sandbox.types import ExecutionResult, ExecutionStatus

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            stdout="",
            stderr="",
            returncode=0,
            execution_time_ms=1.0,
        )

        # Fill cache beyond max size
        start = time.perf_counter()
        for i in range(200):
            cache.set(f"code_{i}", result)
        elapsed = time.perf_counter() - start

        # Should complete eviction quickly
        assert elapsed < 0.1, f"Eviction took {elapsed:.3f}s"
        assert len(cache._cache) == 100  # Max size enforced


class TestSecurityScannerPerformance:
    """Benchmark security scanner performance."""

    def test_scan_simple_code(self) -> None:
        """Test scanning performance for simple code."""
        from src.sandbox.security import SecurityScanner

        scanner = SecurityScanner(SandboxConfig())
        code = 'print("hello")'

        start = time.perf_counter()
        for _ in range(1000):
            scanner.scan_imports(code)
        elapsed = time.perf_counter() - start

        # Should scan 1000 times in under 50ms
        assert elapsed < 0.05, f"Scanning took {elapsed:.3f}s"

    def test_scan_large_code(self) -> None:
        """Test scanning performance for large code."""
        from src.sandbox.security import SecurityScanner

        scanner = SecurityScanner(SandboxConfig())
        # Generate large code
        code = "\n".join([f"x_{i} = {i}" for i in range(1000)])

        start = time.perf_counter()
        scanner.scan_imports(code)
        elapsed = time.perf_counter() - start

        # Should scan large code in under 10ms
        assert elapsed < 0.01, f"Large code scan took {elapsed:.3f}s"


class BenchmarkHelpers:
    """Helper functions for benchmarking."""

    @staticmethod
    def benchmark(func: Callable, iterations: int = 100) -> dict[str, float]:
        """Benchmark a function.

        Args:
            func: Function to benchmark
            iterations: Number of iterations

        Returns:
            Dictionary with benchmark statistics
        """
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            times.append(time.perf_counter() - start)

        return {
            "mean": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "median": sorted(times)[len(times) // 2],
        }

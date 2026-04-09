"""Core execution engine for Code-Sandbox."""

import asyncio
import time

from .cache import ExecutionCache, get_execution_cache
from .security import SandboxSecurityError, SecurityScanner
from .types import ExecutionResult, ExecutionStatus, SandboxConfig


class ExecutionEngine:
    """Async execution engine with security scanning and timeout."""

    def __init__(self, config: SandboxConfig | None = None, use_cache: bool = False):
        """Initialize execution engine.

        Args:
            config: Sandbox configuration. Uses defaults if not provided.
            use_cache: Whether to enable result caching
        """
        self.config = config or SandboxConfig()
        self.scanner = SecurityScanner(self.config)
        self._cache: ExecutionCache | None = (
            get_execution_cache() if use_cache else None
        )

    async def execute(self, code: str, use_cache: bool = False) -> ExecutionResult:
        """Execute Python code in sandbox.

        Args:
            code: Python code to execute (multi-line supported)
            use_cache: Whether to check/use cache for this execution

        Returns:
            ExecutionResult with status, output, and timing information

        Raises:
            SandboxSecurityError: If code contains blocked imports or calls
        """
        start_time = time.time()

        # Check cache first if enabled
        if use_cache and self._cache is not None:
            cached_result = self._cache.get(code)
            if cached_result is not None:
                cached_result.execution_time_ms = (time.time() - start_time) * 1000
                return cached_result

        # Step 1: Security validation
        try:
            self.scanner.validate(code)
        except SyntaxError as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                stdout="",
                stderr=str(e),
                returncode=-1,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message=f"Syntax error: {e}",
            )
        except SandboxSecurityError as e:
            return ExecutionResult(
                status=ExecutionStatus.SECURITY_VIOLATION,
                stdout="",
                stderr="",
                returncode=-1,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
            )

        # Step 2: Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._run_subprocess(code),
                timeout=self.config.timeout_seconds,
            )

            # Cache successful results if enabled
            if use_cache and self._cache is not None:
                self._cache.set(code, result)

            return result
        except asyncio.TimeoutError:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                stdout="",
                stderr="",
                returncode=-1,
                execution_time_ms=self.config.timeout_seconds * 1000,
                error_message=f"Execution timeout after {self.config.timeout_seconds}s",
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                stdout="",
                stderr=str(e),
                returncode=-1,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
            )

    async def _run_subprocess(self, code: str) -> ExecutionResult:
        """Run code in subprocess and capture output.

        Args:
            code: Python code to execute

        Returns:
            ExecutionResult with captured output
        """
        start_time = time.time()

        # Resource limits disabled by default due to platform compatibility
        # Can be enabled with proper configuration for production use
        proc = await asyncio.create_subprocess_exec(
            "python",
            "-c",
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await proc.communicate()

        execution_time_ms = (time.time() - start_time) * 1000

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if proc.returncode == 0:
            status = ExecutionStatus.SUCCESS
        elif proc.returncode == -9:  # SIGKILL (often OOM or resource limit)
            status = ExecutionStatus.ERROR
            stderr += "\n[Process killed - possibly exceeded resource limits]"
        else:
            status = ExecutionStatus.ERROR

        return ExecutionResult(
            status=status,
            stdout=stdout,
            stderr=stderr,
            returncode=proc.returncode,
            execution_time_ms=execution_time_ms,
        )

"""Tests for execution engine."""

import pytest

from src.sandbox.engine import ExecutionEngine
from src.sandbox.types import ExecutionStatus, SandboxConfig


@pytest.fixture
def engine() -> ExecutionEngine:
    """Create engine with default config."""
    return ExecutionEngine(SandboxConfig(timeout_seconds=5))


class TestBasicExecution:
    """Test basic code execution."""

    @pytest.mark.asyncio
    async def test_print_statement(self, engine: ExecutionEngine) -> None:
        """Test basic print statement."""
        result = await engine.execute('print("hello")')
        assert result.status == ExecutionStatus.SUCCESS
        assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_multiline_code(self, engine: ExecutionEngine) -> None:
        """Test multi-line code execution."""
        code = """
x = 1
y = 2
print(f"sum = {x + y}")
"""
        result = await engine.execute(code)
        assert result.status == ExecutionStatus.SUCCESS
        assert "sum = 3" in result.stdout

    @pytest.mark.asyncio
    async def test_expression_evaluation(self, engine: ExecutionEngine) -> None:
        """Test expression evaluation."""
        result = await engine.execute("print(2 + 2 * 3)")
        assert result.status == ExecutionStatus.SUCCESS
        assert "8" in result.stdout


class TestSecurityEnforcement:
    """Test security enforcement during execution."""

    @pytest.mark.asyncio
    async def test_block_os_import(self, engine: ExecutionEngine) -> None:
        """Test that os import is blocked during execution."""
        result = await engine.execute("import os")
        assert result.status == ExecutionStatus.SECURITY_VIOLATION
        assert "os" in result.error_message

    @pytest.mark.asyncio
    async def test_block_subprocess(self, engine: ExecutionEngine) -> None:
        """Test that subprocess import is blocked."""
        result = await engine.execute("import subprocess")
        assert result.status == ExecutionStatus.SECURITY_VIOLATION


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_syntax_error(self, engine: ExecutionEngine) -> None:
        """Test syntax error handling."""
        result = await engine.execute('print("unclosed')
        assert result.status == ExecutionStatus.ERROR
        assert "Syntax error" in result.error_message

    @pytest.mark.asyncio
    async def test_runtime_error(self, engine: ExecutionEngine) -> None:
        """Test runtime error handling."""
        result = await engine.execute("print(1 / 0)")
        assert result.status == ExecutionStatus.ERROR
        assert "ZeroDivisionError" in result.stderr
        assert result.returncode == 1


class TestTimeout:
    """Test timeout enforcement."""

    @pytest.mark.asyncio
    async def test_timeout_enforcement(self) -> None:
        """Test that timeout is enforced."""
        engine = ExecutionEngine(SandboxConfig(timeout_seconds=1))
        result = await engine.execute("import time; time.sleep(5)")
        assert result.status == ExecutionStatus.TIMEOUT
        assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_fast_code_completes(self, engine: ExecutionEngine) -> None:
        """Test that fast code completes before timeout."""
        result = await engine.execute("print('fast')")
        assert result.status == ExecutionStatus.SUCCESS
        assert result.execution_time_ms < 5000  # Should complete in < 5s


class TestExecutionResult:
    """Test execution result structure."""

    @pytest.mark.asyncio
    async def test_returncode_captured(self, engine: ExecutionEngine) -> None:
        """Test that return code is captured."""
        # Note: Can't test sys.exit since sys is blocked
        # Test with a runtime error instead
        result = await engine.execute("print(1 / 0)")
        assert result.returncode == 1

    @pytest.mark.asyncio
    async def test_execution_time_recorded(self, engine: ExecutionEngine) -> None:
        """Test that execution time is recorded."""
        result = await engine.execute("print('test')")
        assert result.execution_time_ms >= 0
        assert result.execution_time_ms < 5000  # Should be fast

    @pytest.mark.asyncio
    async def test_stdout_captured(self, engine: ExecutionEngine) -> None:
        """Test that stdout is captured."""
        result = await engine.execute("print('hello world')")
        assert "hello world" in result.stdout

    @pytest.mark.asyncio
    async def test_stderr_captured(self, engine: ExecutionEngine) -> None:
        """Test that stderr is captured."""
        result = await engine.execute(
            "import sys; print('error message', file=sys.stderr)"
        )
        # Note: sys is blocked, so this will be a security violation
        # Test with a runtime error instead
        result = await engine.execute("print(1 / 0)")
        assert "ZeroDivisionError" in result.stderr

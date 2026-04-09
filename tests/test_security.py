"""Tests for security module."""

import pytest

from src.sandbox.security import SandboxSecurityError, SecurityScanner
from src.sandbox.types import SandboxConfig


@pytest.fixture
def scanner() -> SecurityScanner:
    """Create scanner with default config."""
    return SecurityScanner(SandboxConfig())


class TestBlockedImports:
    """Test blocked import detection."""

    def test_block_os_import(self, scanner: SecurityScanner) -> None:
        """Test that os module is blocked."""
        with pytest.raises(SandboxSecurityError) as exc_info:
            scanner.validate("import os")
        assert "os" in exc_info.value.violations

    def test_block_subprocess_import(self, scanner: SecurityScanner) -> None:
        """Test that subprocess module is blocked."""
        with pytest.raises(SandboxSecurityError) as exc_info:
            scanner.validate("import subprocess")
        assert "subprocess" in exc_info.value.violations

    def test_block_sys_import(self, scanner: SecurityScanner) -> None:
        """Test that sys module is blocked."""
        with pytest.raises(SandboxSecurityError) as exc_info:
            scanner.validate("import sys")
        assert "sys" in exc_info.value.violations

    def test_block_ctypes_import(self, scanner: SecurityScanner) -> None:
        """Test that ctypes module is blocked."""
        with pytest.raises(SandboxSecurityError) as exc_info:
            scanner.validate("import ctypes")
        assert "ctypes" in exc_info.value.violations

    def test_block_from_import(self, scanner: SecurityScanner) -> None:
        """Test that 'from os import x' is blocked."""
        with pytest.raises(SandboxSecurityError) as exc_info:
            scanner.validate("from os import system")
        assert "os" in exc_info.value.violations


class TestDangerousCalls:
    """Test dangerous function call detection."""

    def test_block_eval(self, scanner: SecurityScanner) -> None:
        """Test that eval() is blocked."""
        with pytest.raises(SandboxSecurityError) as exc_info:
            scanner.validate("eval('1+1')")
        assert "eval()" in exc_info.value.violations

    def test_block_exec(self, scanner: SecurityScanner) -> None:
        """Test that exec() is blocked."""
        with pytest.raises(SandboxSecurityError) as exc_info:
            scanner.validate("exec('print(1)')")
        assert "exec()" in exc_info.value.violations

    def test_block_compile(self, scanner: SecurityScanner) -> None:
        """Test that compile() is blocked."""
        with pytest.raises(SandboxSecurityError) as exc_info:
            scanner.validate("compile('1+1', '', 'eval')")
        assert "compile()" in exc_info.value.violations


class TestAllowedImports:
    """Test that safe imports are allowed."""

    def test_allow_math_import(self, scanner: SecurityScanner) -> None:
        """Test that math module is allowed."""
        scanner.validate("import math")  # Should not raise

    def test_allow_numpy_import(self, scanner: SecurityScanner) -> None:
        """Test that numpy is allowed."""
        scanner.validate("import numpy as np")  # Should not raise

    def test_allow_pandas_import(self, scanner: SecurityScanner) -> None:
        """Test that pandas is allowed."""
        scanner.validate("import pandas as pd")  # Should not raise

    def test_allow_json_import(self, scanner: SecurityScanner) -> None:
        """Test that json is allowed."""
        scanner.validate("import json")  # Should not raise

    def test_allow_safe_code(self, scanner: SecurityScanner) -> None:
        """Test that safe code passes validation."""
        code = """
import math
import json

result = math.sqrt(16)
data = {"value": result}
print(json.dumps(data))
"""
        scanner.validate(code)  # Should not raise

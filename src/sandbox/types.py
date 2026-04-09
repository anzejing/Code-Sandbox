"""Type definitions for Code-Sandbox."""

import time
from dataclasses import dataclass, field
from enum import Enum


class ExecutionStatus(Enum):
    """Execution result status."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class ExecutionResult:
    """Result of code execution."""

    status: ExecutionStatus
    stdout: str
    stderr: str
    returncode: int | None
    execution_time_ms: float
    error_message: str | None = None

    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""

    timeout_seconds: int = 30
    max_memory_mb: int = 512
    allowed_modules: list[str] = field(default_factory=list)
    blocked_modules: list[str] = field(
        default_factory=lambda: [
            "os",
            "subprocess",
            "sys",
            "builtins",
            "ctypes",
            "socket",
            "pickle",
            "shelve",
        ]
    )

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_memory_mb <= 0:
            raise ValueError("max_memory_mb must be positive")


@dataclass
class PlotResource:
    """Resource for storing plot images."""

    id: str
    image_bytes: bytes
    mime_type: str = "image/png"
    created_at: float = field(default_factory=time.time)

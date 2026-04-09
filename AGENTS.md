# AGENTS.md - Code-Sandbox MCP Server

## Project Overview
FastMCP-based Python execution sandbox for AI agents. Provides secure, type-safe code execution with dependency management and progress reporting.

## Build & Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the MCP server
python -m src.server

# Run tests
pytest                    # All tests
pytest tests/test_exec.py # Single test file
pytest -k test_sandbox    # Single test by name

# Linting & Formatting
ruff check src/           # Lint
ruff format src/          # Format
mypy src/                 # Type checking

# Security scan
bandit -r src/            # Security vulnerabilities
```

## Code Style Guidelines

### Imports
```python
# Standard library → third-party → local, grouped with blank lines
import asyncio
from typing import Optional, List, Dict

import numpy as np
from fastmcp import FastMCP, Context

from .sandbox import ExecutionEngine
```
- Use absolute imports within `src/`
- Remove unused imports (ruff enforces)

### Type Hints
- **Required** on all function signatures (parameters and return types)
- Use `Optional[T]` for nullable values, `TypedDict` for structured data
- Annotate async functions: `async def execute(...) -> ExecutionResult:`

### Naming Conventions
- **Classes**: PascalCase (`ExecutionEngine`, `SandboxConfig`)
- **Functions/Methods**: snake_case (`execute_code`, `validate_imports`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`, `MAX_MEMORY_MB`)
- **Private**: Leading underscore (`_validate_code`, `_scan_for_dangerous_imports`)

### Async Patterns
- Prefer `async def` for all I/O-bound operations
- Use `asyncio.gather()` for parallel execution
- Timeout handling: `asyncio.wait_for(coro, timeout=seconds)`

### Error Handling
```python
class SandboxExecutionError(Exception):
    def __init__(self, message: str, stderr: str = ""):
        self.stderr = stderr
        super().__init__(message)

try:
    result = await engine.execute(code)
except TimeoutError as e:
    raise SandboxExecutionError("Execution timeout", stderr="") from e
```
- Never bare `except:` - always specify exception type
- Include original exception with `from e`
- Log errors with context before re-raising

### Docstrings
```python
@mcp.tool()
async def execute_python(ctx: Context, code: str, timeout: int = 30) -> ExecutionResult:
    """Execute Python code in isolated sandbox.

    Args:
        ctx: FastMCP context for progress reporting
        code: Python code to execute (multi-line supported)
        timeout: Maximum execution time in seconds (default: 30)

    Returns:
        ExecutionResult with stdout, stderr, and return value

    Raises:
        SandboxExecutionError: If code contains dangerous imports
    """
```

### Security Rules
1. **Never** allow direct `os.system()`, `subprocess`, `eval()` on user input
2. **Always** validate imports against allowlist before execution
3. **Always** enforce timeout on code execution
4. **Never** expose host filesystem paths in error messages

## Architecture

```
src/
├── server.py          # FastMCP entry point, tool registration
├── sandbox/
│   ├── __init__.py
│   ├── engine.py      # Core execution logic
│   ├── security.py    # Import validation, code scanning
│   └── types.py       # TypedDict, dataclasses, enums
└── utils/
    └── logging.py     # Structured logging setup
```

## Testing Patterns
```python
import pytest
from src.sandbox.engine import ExecutionEngine

@pytest.mark.asyncio
async def test_basic_execution():
    engine = ExecutionEngine(timeout=5)
    result = await engine.execute("print('hello')")
    assert result.stdout.strip() == "hello"
    assert result.returncode == 0
```
- Use `pytest-asyncio` for async tests
- Mock external dependencies with `pytest-mock`
- Test security boundaries explicitly

## MCP Configuration (claude_desktop_config.json)
```json
{
  "mcpServers": {
    "code-sandbox": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/python-sandbox",
      "env": { "PYTHONPATH": "/path/to/python-sandbox" }
    }
  }
}
```

## Debugging with Inspector
```bash
# Terminal 1: Start server
python -m src.server

# Terminal 2: Run inspector
npx @modelcontextprotocol/inspector
# Connect to localhost:3000, select "code-sandbox" server
```

## FastMCP-Specific Patterns

### Tool Registration with Progress
```python
@mcp.tool()
async def execute_python(ctx: Context, code: str) -> str:
    await ctx.report_progress(0, 100, "Validating code...")
    await ctx.report_progress(100, 100, "Complete")
    return result
```

### Resource Handling (for images/plots)
```python
@mcp.resource("plot://{id}")
async def get_plot(id: str) -> tuple[bytes, str]:
    """Return plot image with MIME type."""
    return image_bytes, "image/png"
```

### Dependencies Declaration
```python
@mcp.tool(dependencies=["numpy", "pandas", "matplotlib"])
async def analyze_data(code: str) -> str:
    """Execute data analysis code with auto-installed deps."""
```

## Key Reminders
- **Type safety first**: If unsure about a type, use `Any` temporarily and add TODO
- **Fail fast**: Validate inputs at function boundaries
- **Log structured**: Use `logging.info()` with context, not `print()`
- **Test security**: Every new tool needs security boundary tests

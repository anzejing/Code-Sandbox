"""FastMCP server for Code-Sandbox."""

from fastmcp import Context, FastMCP

from .sandbox.engine import ExecutionEngine
from .sandbox.plots import get_plot_cache
from .sandbox.types import ExecutionResult, ExecutionStatus, SandboxConfig

# Create MCP server instance
mcp = FastMCP("Code-Sandbox")

# Initialize execution engine with default config
_engine: ExecutionEngine | None = None


def get_engine() -> ExecutionEngine:
    """Get or create execution engine singleton."""
    global _engine
    if _engine is None:
        _engine = ExecutionEngine(SandboxConfig(timeout_seconds=30))
    return _engine


@mcp.tool()
async def execute_python(
    ctx: Context,
    code: str,
    timeout: int = 30,
) -> str:
    """Execute Python code in isolated sandbox.

    Args:
        ctx: FastMCP context for progress reporting
        code: Python code to execute (multi-line supported)
        timeout: Maximum execution time in seconds (default: 30)

    Returns:
        Formatted string with stdout, stderr, and execution status

    Raises:
        SandboxSecurityError: If code contains blocked imports or dangerous calls
    """
    engine = get_engine()
    engine.config.timeout_seconds = timeout

    await ctx.report_progress(0, 100, "Validating code...")

    result = await engine.execute(code)

    await ctx.report_progress(100, 100, "Complete")

    return _format_result(result)


@mcp.tool()
async def analyze_data(
    ctx: Context,
    code: str,
    timeout: int = 60,
) -> str:
    """Execute data analysis code with numpy, pandas, matplotlib support.

    Note: Requires numpy, pandas, matplotlib to be installed in the environment.
    Install with: pip install numpy pandas matplotlib

    Args:
        ctx: FastMCP context for progress reporting
        code: Python code to execute (multi-line supported)
        timeout: Maximum execution time in seconds (default: 60)

    Returns:
        Formatted string with stdout, stderr, and execution status
    """
    return await execute_python(ctx, code, timeout)


@mcp.tool()
async def check_security(
    ctx: Context,
    code: str,
) -> str:
    """Check code for security violations without executing.

    Use this to validate code safety before execution.

    Args:
        ctx: FastMCP context for progress reporting
        code: Python code to check

    Returns:
        Security check result with any violations found
    """
    await ctx.report_progress(0, 100, "Scanning code...")

    engine = get_engine()
    try:
        engine.scanner.validate(code)
        await ctx.report_progress(100, 100, "Complete")
        return "✓ Code passed security check - no violations detected"
    except Exception as e:
        await ctx.report_progress(100, 100, "Complete")
        return f"✗ Security violations detected: {e}"


@mcp.resource("plot://{id}")
async def get_plot(id: str) -> tuple[bytes, str]:
    """Retrieve plot image by ID.

    Args:
        id: Plot resource ID

    Returns:
        Tuple of (image_bytes, mime_type)

    Raises:
        KeyError: If plot ID not found
    """
    cache = get_plot_cache()
    resource = cache.get(id)
    if resource is None:
        raise KeyError(f"Plot not found: {id}")
    return resource.image_bytes, resource.mime_type


@mcp.tool()
async def store_plot(
    ctx: Context,
    image_base64: str,
    mime_type: str = "image/png",
) -> str:
    """Store a plot image and return its resource ID.

    Args:
        ctx: FastMCP context for progress reporting
        image_base64: Base64-encoded image data
        mime_type: MIME type of the image (default: image/png)

    Returns:
        Resource ID for retrieving the image via plot:// URI
    """
    import base64

    await ctx.report_progress(0, 100, "Decoding image...")

    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        return f"✗ Failed to decode image: {e}"

    cache = get_plot_cache()
    plot_id = cache.store(image_bytes, mime_type)

    await ctx.report_progress(100, 100, "Complete")

    return f"✓ Plot stored. Access via: plot://{plot_id}"


def _format_result(result: ExecutionResult) -> str:
    """Format execution result for display.

    Args:
        result: Execution result to format

    Returns:
        Formatted string with status, output, and timing
    """
    lines = []

    # Status line
    status_icon = {
        ExecutionStatus.SUCCESS: "✓",
        ExecutionStatus.ERROR: "✗",
        ExecutionStatus.TIMEOUT: "⏱",
        ExecutionStatus.SECURITY_VIOLATION: "🚫",
    }.get(result.status, "?")

    lines.append(f"{status_icon} Status: {result.status.value}")

    # Timing
    lines.append(f"⏱ Execution time: {result.execution_time_ms:.2f}ms")

    # Return code (if available)
    if result.returncode is not None and result.returncode != -1:
        lines.append(f"📊 Return code: {result.returncode}")

    # Stdout
    if result.stdout:
        lines.append("\n📤 stdout:")
        lines.append(result.stdout)

    # Stderr
    if result.stderr:
        lines.append("\n📥 stderr:")
        lines.append(result.stderr)

    # Error message
    if result.error_message:
        lines.append(f"\n⚠️  {result.error_message}")

    return "\n".join(lines)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

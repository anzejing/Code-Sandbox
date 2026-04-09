"""Tests for MCP server tools."""

import pytest

from src.server import get_engine, mcp


class TestServerSetup:
    """Test server initialization."""

    def test_engine_singleton(self) -> None:
        """Test that engine is a singleton."""
        engine1 = get_engine()
        engine2 = get_engine()
        assert engine1 is engine2

    def test_engine_default_timeout(self) -> None:
        """Test engine default timeout."""
        engine = get_engine()
        assert engine.config.timeout_seconds == 30


class TestToolRegistration:
    """Test tool registration."""

    @pytest.mark.asyncio
    async def test_tools_registered(self) -> None:
        """Test that tools are registered."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "execute_python" in tool_names
        assert "analyze_data" in tool_names
        assert "check_security" in tool_names


class TestExecutePython:
    """Test execute_python tool."""

    @pytest.mark.asyncio
    async def test_execute_basic_code(self) -> None:
        """Test basic code execution via tool."""
        from fastmcp import Context

        from src.server import execute_python

        # Create context through MCP
        ctx = Context(fastmcp=mcp)
        result = await execute_python(ctx, 'print("hello")')
        assert "hello" in result
        assert "Status: success" in result

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self) -> None:
        """Test code execution with custom timeout."""
        from fastmcp import Context

        from src.server import execute_python

        ctx = Context(fastmcp=mcp)
        result = await execute_python(ctx, 'print("fast")', timeout=10)
        assert "fast" in result


class TestAnalyzeData:
    """Test analyze_data tool."""

    @pytest.mark.asyncio
    async def test_analyze_data_registered(self) -> None:
        """Test that analyze_data tool is available."""
        tools = await mcp.list_tools()
        analyze_tool = next((t for t in tools if t.name == "analyze_data"), None)
        assert analyze_tool is not None
        assert "data analysis" in analyze_tool.description.lower()


class TestCheckSecurity:
    """Test check_security tool."""

    @pytest.mark.asyncio
    async def test_check_safe_code(self) -> None:
        """Test security check with safe code."""
        from fastmcp import Context

        from src.server import check_security

        ctx = Context(fastmcp=mcp)
        result = await check_security(ctx, "import math; print(2 + 2)")
        assert "passed" in result.lower()

    @pytest.mark.asyncio
    async def test_check_unsafe_code(self) -> None:
        """Test security check with unsafe code."""
        from fastmcp import Context

        from src.server import check_security

        ctx = Context(fastmcp=mcp)
        result = await check_security(ctx, "import os")
        assert "violation" in result.lower()


class TestPlotTools:
    """Test plot-related tools."""

    @pytest.mark.asyncio
    async def test_store_plot(self) -> None:
        """Test storing a plot image."""
        import base64

        from fastmcp import Context

        from src.server import store_plot

        ctx = Context(fastmcp=mcp)
        image_bytes = b"fake_png_data"
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        result = await store_plot(ctx, image_base64)
        assert "Plot stored" in result
        assert "plot://" in result

    @pytest.mark.asyncio
    async def test_store_plot_invalid_base64(self) -> None:
        """Test storing plot with invalid base64."""
        from fastmcp import Context

        from src.server import store_plot

        ctx = Context(fastmcp=mcp)
        result = await store_plot(ctx, "invalid_base64!!!")
        assert "Failed to decode" in result

    @pytest.mark.asyncio
    async def test_get_plot_resource(self) -> None:
        """Test retrieving a plot resource."""

        from src.sandbox.plots import get_plot_cache

        # Store a plot first
        cache = get_plot_cache()
        image_bytes = b"test_image_data"
        plot_id = cache.store(image_bytes)

        # Retrieve via resource handler
        from src.server import get_plot

        retrieved_bytes, mime_type = await get_plot(plot_id)
        assert retrieved_bytes == image_bytes
        assert mime_type == "image/png"

    @pytest.mark.asyncio
    async def test_get_plot_not_found(self) -> None:
        """Test retrieving nonexistent plot."""
        from src.server import get_plot

        with pytest.raises(KeyError):
            await get_plot("nonexistent-id")

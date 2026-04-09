"""Tests for plot cache module."""

from src.sandbox.plots import PlotCache, get_plot_cache


class TestPlotCache:
    """Test plot cache functionality."""

    def test_store_and_retrieve(self) -> None:
        """Test storing and retrieving a plot."""
        cache = PlotCache()
        image_bytes = b"fake_png_data"

        plot_id = cache.store(image_bytes)
        assert plot_id is not None

        resource = cache.get(plot_id)
        assert resource is not None
        assert resource.image_bytes == image_bytes
        assert resource.mime_type == "image/png"

    def test_store_with_custom_mime(self) -> None:
        """Test storing with custom MIME type."""
        cache = PlotCache()
        image_bytes = b"fake_svg_data"

        plot_id = cache.store(image_bytes, mime_type="image/svg+xml")
        resource = cache.get(plot_id)
        assert resource is not None
        assert resource.mime_type == "image/svg+xml"

    def test_get_nonexistent(self) -> None:
        """Test retrieving nonexistent plot."""
        cache = PlotCache()
        resource = cache.get("nonexistent-id")
        assert resource is None

    def test_get_base64(self) -> None:
        """Test retrieving plot as base64."""
        cache = PlotCache()
        image_bytes = b"test_data"

        plot_id = cache.store(image_bytes)
        base64_str = cache.get_base64(plot_id)

        assert base64_str is not None
        import base64

        decoded = base64.b64decode(base64_str)
        assert decoded == image_bytes

    def test_cache_cleanup(self) -> None:
        """Test cache cleanup of expired entries."""
        cache = PlotCache(ttl_seconds=0)  # Immediate expiry
        image_bytes = b"test_data"

        plot_id = cache.store(image_bytes)
        # Should be expired immediately
        import time

        time.sleep(0.01)
        resource = cache.get(plot_id)
        assert resource is None

    def test_max_size_enforcement(self) -> None:
        """Test cache max size enforcement."""
        cache = PlotCache(max_size=3)

        # Store 5 items
        ids = [cache.store(f"data_{i}".encode()) for i in range(5)]

        # Should only have 3 items
        assert len(cache._cache) == 3

        # Oldest items should be removed
        assert cache.get(ids[0]) is None
        assert cache.get(ids[1]) is None
        assert cache.get(ids[2]) is not None

    def test_clear_cache(self) -> None:
        """Test clearing cache."""
        cache = PlotCache()
        cache.store(b"data1")
        cache.store(b"data2")

        cache.clear()
        assert len(cache._cache) == 0

    def test_singleton(self) -> None:
        """Test get_plot_cache returns singleton."""
        cache1 = get_plot_cache()
        cache2 = get_plot_cache()
        assert cache1 is cache2

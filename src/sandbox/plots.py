"""Plot resource handling for Code-Sandbox."""

import base64
import time
import uuid

from .types import PlotResource


class PlotCache:
    """In-memory cache for plot images."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """Initialize plot cache.

        Args:
            max_size: Maximum number of plots to cache
            ttl_seconds: Time-to-live for cached plots
        """
        self._cache: dict[str, PlotResource] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds

    def store(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """Store plot image and return resource ID.

        Args:
            image_bytes: Image data bytes
            mime_type: MIME type of the image

        Returns:
            Resource ID for retrieving the image
        """
        # Clean up expired entries
        self._cleanup()

        # Generate unique ID
        plot_id = str(uuid.uuid4())

        # Store in cache
        self._cache[plot_id] = PlotResource(
            id=plot_id,
            image_bytes=image_bytes,
            mime_type=mime_type,
            created_at=time.time(),
        )

        # Enforce max size
        if len(self._cache) > self._max_size:
            # Remove oldest entry
            oldest_id = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
            del self._cache[oldest_id]

        return plot_id

    def get(self, plot_id: str) -> PlotResource | None:
        """Retrieve plot by ID.

        Args:
            plot_id: Resource ID

        Returns:
            PlotResource if found and not expired, None otherwise
        """
        resource = self._cache.get(plot_id)
        if resource is None:
            return None

        # Check if expired
        if time.time() - resource.created_at > self._ttl_seconds:
            del self._cache[plot_id]
            return None

        return resource

    def get_base64(self, plot_id: str) -> str | None:
        """Retrieve plot as base64 string.

        Args:
            plot_id: Resource ID

        Returns:
            Base64-encoded image string or None if not found
        """
        resource = self.get(plot_id)
        if resource is None:
            return None

        return base64.b64encode(resource.image_bytes).decode("utf-8")

    def _cleanup(self) -> None:
        """Remove expired entries from cache."""
        now = time.time()
        expired = [
            k for k, v in self._cache.items() if now - v.created_at > self._ttl_seconds
        ]
        for key in expired:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cached plots."""
        self._cache.clear()


# Global cache instance
_plot_cache: PlotCache | None = None


def get_plot_cache() -> PlotCache:
    """Get or create plot cache singleton."""
    global _plot_cache
    if _plot_cache is None:
        _plot_cache = PlotCache()
    return _plot_cache

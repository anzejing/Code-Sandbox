"""Logging configuration for Code-Sandbox."""

import logging
import sys


def setup_logging(
    level: int = logging.INFO,
    format_string: str | None = None,
) -> logging.Logger:
    """Setup structured logging for the application.

    Args:
        level: Logging level (default: INFO)
        format_string: Custom log format (optional)

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Create logger
    logger = logging.getLogger("code-sandbox")
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def get_logger(name: str = "code-sandbox") -> logging.Logger:
    """Get logger instance.

    Args:
        name: Logger name (default: code-sandbox)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Default logger instance
logger = setup_logging()

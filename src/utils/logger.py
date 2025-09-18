import logging
import sys
from typing import Optional

# Define log levels with emojis for better visibility
LOG_LEVELS = {"DEBUG": "🔍", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "🚨"}


class CustomFormatter(logging.Formatter):
    """Custom formatter adding emojis and colors to logs"""

    def format(self, record):
        # Add emoji to the log level
        level_emoji = LOG_LEVELS.get(record.levelname, "")
        record.levelname = f"{level_emoji} {record.levelname}"
        return super().format(record)


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Creates a logger with consistent formatting and configuration

    Args:
        name: The name of the logger (usually __name__)
        level: Optional logging level (defaults to INFO)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)

    # Avoid adding handlers if they already exist
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)

        # Create formatter
        formatter = CustomFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Add formatter to handler
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

    # Set level (default to INFO if not specified)
    logger.setLevel(level or logging.INFO)

    return logger

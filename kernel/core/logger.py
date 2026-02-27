"""
Structured Logging Module for Project Genesis Core Kernel.

Provides centralized logging with:
- Console Handler: Human-readable output
- File Handler: Machine-readable JSON Lines (kernel.log.jsonl)
"""

import logging
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON Lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        # Add optional data payload if present
        if hasattr(record, "data") and record.data:
            log_entry["data"] = record.data

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter with color support."""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        level = f"{color}{record.levelname:8s}{self.COLORS['RESET']}"
        module = f"{record.module:20s}"

        base_msg = f"{timestamp} | {level} | {module} | {record.getMessage()}"

        # Add data payload if present
        if hasattr(record, "data") and record.data:
            base_msg += f" | data: {json.dumps(record.data)}"

        return base_msg


class KernelLogger:
    """
    Centralized logger for Project Genesis Core Kernel.

    Usage:
        from kernel.core.logger import logger

        logger.info("Plugin loaded", data={"name": "avatar"})
        logger.error("Connection failed", data={"host": "localhost", "port": 5432})
    """

    _instance: Optional[logging.Logger] = None
    _initialized: bool = False

    @classmethod
    def get_logger(cls, name: str = "genesis", log_dir: str = "kernel") -> logging.Logger:
        """
        Get or create the centralized logger instance.

        Args:
            name: Logger name (default: "genesis")
            log_dir: Directory for log file (relative to project root)

        Returns:
            Configured logger instance
        """
        if cls._instance is not None:
            return cls._instance

        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        # Determine log file path
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        log_file_path = project_root / f"{log_dir}.log.jsonl"

        # Create file handler (JSON Lines)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())

        # Create console handler (Human-readable)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ConsoleFormatter())

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        cls._instance = logger
        cls._initialized = True

        return logger


# Convenience function for easy importing
def get_logger(name: str = "genesis") -> logging.Logger:
    """Get the kernel logger instance."""
    return KernelLogger.get_logger(name)


# Default logger instance
logger = KernelLogger.get_logger("genesis")


def log(level: int, message: str, data: Optional[dict] = None):
    """
    Log a message with optional data payload.

    Args:
        level: Logging level (logging.DEBUG, logging.INFO, etc.)
        message: Log message
        data: Optional dictionary with additional context data
    """
    if data:
        # Use a custom log record with data attribute
        extra = {"data": data}
        logger.log(level, message, extra=extra)
    else:
        logger.log(level, message)


# Convenience functions
def debug(message: str, data: Optional[dict] = None):
    """Log debug message."""
    log(logging.DEBUG, message, data)


def info(message: str, data: Optional[dict] = None):
    """Log info message."""
    log(logging.INFO, message, data)


def warning(message: str, data: Optional[dict] = None):
    """Log warning message."""
    log(logging.WARNING, message, data)


def error(message: str, data: Optional[dict] = None):
    """Log error message."""
    log(logging.ERROR, message, data)


def critical(message: str, data: Optional[dict] = None):
    """Log critical message."""
    log(logging.CRITICAL, message, data)

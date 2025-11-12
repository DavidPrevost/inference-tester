"""Standardized error handling and messages for LLM Inference Tester.

This module provides consistent error messages and exception handling
across the application.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class InferenceTesterError(Exception):
    """Base exception for all LLM Inference Tester errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        """Initialize the error.

        Args:
            message: Primary error message
            details: Additional context or details
        """
        self.message = message
        self.details = details
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format the error message with details.

        Returns:
            Formatted error message
        """
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class ConfigurationError(InferenceTesterError):
    """Raised when there's a configuration error."""
    pass


class ModelError(InferenceTesterError):
    """Raised when there's a model-related error."""
    pass


class ServerError(InferenceTesterError):
    """Raised when there's a server-related error."""
    pass


class TestError(InferenceTesterError):
    """Raised when a test fails to execute."""
    pass


def format_error_message(
    error_type: str,
    context: str,
    details: Optional[str] = None,
    suggestion: Optional[str] = None
) -> str:
    """Format a standardized error message.

    Args:
        error_type: Type of error (e.g., "Configuration Error")
        context: Context where error occurred
        details: Detailed error information
        suggestion: Suggested resolution

    Returns:
        Formatted error message
    """
    message = f"{error_type} in {context}"

    if details:
        message += f": {details}"

    if suggestion:
        message += f"\nSuggestion: {suggestion}"

    return message


def log_and_raise(
    exception_class: type,
    message: str,
    details: Optional[str] = None,
    log_level: int = logging.ERROR
):
    """Log an error and raise an exception.

    Args:
        exception_class: Exception class to raise
        message: Primary error message
        details: Additional details
        log_level: Logging level to use

    Raises:
        The specified exception class
    """
    full_message = message
    if details:
        full_message = f"{message}: {details}"

    logger.log(log_level, full_message)
    raise exception_class(message, details)

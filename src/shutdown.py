"""Shared shutdown state for graceful termination.

This module provides a global shutdown flag that can be accessed
by multiple modules to coordinate graceful shutdown.
"""

# Global flag for graceful shutdown
_shutdown_requested = False


def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested.

    Returns:
        True if shutdown was requested, False otherwise
    """
    global _shutdown_requested
    return _shutdown_requested


def request_shutdown() -> None:
    """Request graceful shutdown."""
    global _shutdown_requested
    _shutdown_requested = True


def reset_shutdown() -> None:
    """Reset shutdown flag (mainly for testing)."""
    global _shutdown_requested
    _shutdown_requested = False

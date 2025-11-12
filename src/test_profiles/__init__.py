"""Test profile modules for different use cases.

This package contains test profile implementations for various LLM use cases.
Each profile tests specific aspects of performance relevant to its use case.
"""

import logging

logger = logging.getLogger(__name__)

# Profile registry - populated when individual profiles are implemented
PROFILES = {}


def get_profile(name: str):
    """Get a test profile by name.

    Args:
        name: Profile name (e.g., "interactive", "batch")

    Returns:
        Profile instance

    Raises:
        ValueError: If profile not found

    """
    if name not in PROFILES:
        raise ValueError(f"Unknown profile: {name}. Available: {list(PROFILES.keys())}")

    return PROFILES[name]()


def list_profiles() -> list:
    """Get list of available profile names.

    Returns:
        List of profile names

    """
    return list(PROFILES.keys())

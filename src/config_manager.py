"""Configuration management for LLM Inference Tester.

This module handles loading, validating, and managing configuration files
(config.yaml and models.yaml). It provides default values and validates
user configurations against expected schemas.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and validation.

    Loads both test configuration (config.yaml) and model definitions
    (models.yaml), validates them, and provides a unified interface
    for accessing configuration values throughout the application.
    """

    def __init__(self, config_path: Path, models_path: Path):
        """Initialize the ConfigManager.

        Args:
            config_path: Path to config.yaml
            models_path: Path to models.yaml

        """
        self.config_path = config_path
        self.models_path = models_path
        self.config: Dict[str, Any] = {}
        self.models: List[Dict[str, Any]] = []

    def load(self):
        """Load and validate all configuration files.

        Raises:
            FileNotFoundError: If configuration files don't exist
            ValueError: If configuration is invalid

        """
        logger.info("Loading configuration from %s", self.config_path)
        # TODO: Implement configuration loading
        pass

    def validate(self):
        """Validate configuration against schema.

        Raises:
            ValueError: If configuration is invalid

        """
        logger.debug("Validating configuration")
        # TODO: Implement validation
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., "llama_cpp.server_path")
            default: Default value if key not found

        Returns:
            Configuration value or default

        """
        # TODO: Implement nested key access
        return self.config.get(key, default)

    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of model definitions.

        Returns:
            List of model configuration dictionaries

        """
        return self.models

    def get_thresholds(self, profile: str) -> Dict[str, float]:
        """Get threshold values for a specific test profile.

        Args:
            profile: Profile name (e.g., "interactive", "batch")

        Returns:
            Dictionary of threshold values for the profile

        """
        # TODO: Implement threshold retrieval
        return {}

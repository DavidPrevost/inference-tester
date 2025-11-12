"""Configuration management for LLM Inference Tester.

This module handles loading, validating, and managing configuration files
(config.yaml and models.yaml). It provides default values and validates
user configurations against expected schemas.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


# Default configuration values
DEFAULT_CONFIG = {
    "llama_cpp": {
        "server_path": "./llama-server",
        "default_ctx_size": 8192,
        "default_threads": None,
        "gpu_layers": 0
    },
    "test_mode": "full",
    "resume_from": None,
    "profiles": ["interactive", "long_context", "batch", "quality", "stress"],
    "thresholds": {
        "interactive": {
            "min_tokens_per_sec": 2,
            "max_time_to_first_token": 30,
            "max_variance": 20
        },
        "long_context": {
            "max_initial_load_time": 60,
            "test_sizes": [4096, 8192, 16384, 32768]
        },
        "batch": {
            "max_variance": 20,
            "num_documents": 30
        },
        "quality": {
            "min_math_score": 80,
            "min_comprehension_score": 75,
            "min_reasoning_score": 75,
            "min_format_compliance": 90
        },
        "stress": {
            "duration": 30,
            "max_temperature": 85,
            "sample_interval": 30
        }
    },
    "limits": {
        "max_memory_gb": 14,
        "max_load_time": 300,
        "allow_swap": False
    },
    "model_dir": "./models",
    "output": {
        "dir": "./results",
        "formats": ["json", "csv", "html"],
        "include_logs": True
    },
    "logging": {
        "level": "INFO",
        "file": "inference-tester.log"
    },
    "advanced": {
        "port_range_start": 8080,
        "port_range_end": 8180,
        "color_output": True,
        "show_progress": True
    }
}


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
        self.config_path = Path(config_path)
        self.models_path = Path(models_path)
        self.config: Dict[str, Any] = {}
        self.models: List[Dict[str, Any]] = []
        self._loaded = False

    def load(self):
        """Load and validate all configuration files.

        Raises:
            FileNotFoundError: If configuration files don't exist
            ValueError: If configuration is invalid

        """
        logger.info("Loading configuration from %s", self.config_path)

        # Start with default config
        self.config = self._deep_merge(DEFAULT_CONFIG.copy(), {})

        # Load user config if it exists
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
            self.config = self._deep_merge(self.config, user_config)
            logger.debug("Loaded user configuration from %s", self.config_path)
        else:
            logger.warning("Config file %s not found, using defaults", self.config_path)

        # Load models config
        if not self.models_path.exists():
            raise FileNotFoundError(f"Models configuration not found: {self.models_path}")

        with open(self.models_path, 'r') as f:
            models_data = yaml.safe_load(f)
            self.models = models_data.get('models', [])

            # Store quant configurations for easy access
            self.quick_mode_quants = models_data.get('quick_mode_quants', ['Q4_K_M', 'Q5_K_M'])
            self.full_mode_quants = models_data.get('full_mode_quants',
                ['Q2_K', 'Q3_K_M', 'Q4_K_M', 'Q5_K_M', 'Q6_K', 'Q8_0'])

        logger.info("Loaded %d model definitions", len(self.models))

        # Validate configuration
        self.validate()
        self._loaded = True

    def validate(self):
        """Validate configuration against schema.

        Raises:
            ValueError: If configuration is invalid

        """
        logger.debug("Validating configuration")

        # Validate llama_cpp settings
        if "llama_cpp" not in self.config:
            raise ValueError("Missing required section: llama_cpp")

        llama_config = self.config["llama_cpp"]
        if "server_path" not in llama_config:
            raise ValueError("Missing required setting: llama_cpp.server_path")

        # Validate and sanitize paths
        self._validate_path(llama_config["server_path"], "llama_cpp.server_path")

        # Validate thresholds
        if "thresholds" not in self.config:
            raise ValueError("Missing required section: thresholds")

        # Validate model_dir exists or can be created
        model_dir = Path(self.config.get("model_dir", "./models"))
        self._validate_path(model_dir, "model_dir", must_exist=False)
        if not model_dir.exists():
            logger.info("Model directory %s doesn't exist, will create it", model_dir)

        # Validate output dir exists or can be created
        output_dir = Path(self.config["output"]["dir"])
        self._validate_path(output_dir, "output.dir", must_exist=False)
        if not output_dir.exists():
            logger.info("Output directory %s doesn't exist, will create it", output_dir)

        # Validate test_mode
        test_mode = self.config.get("test_mode")
        if test_mode not in ["quick", "full"]:
            raise ValueError(f"Invalid test_mode: {test_mode}. Must be 'quick' or 'full'")

        # Validate numeric ranges
        self._validate_numeric_ranges()

        logger.debug("Configuration validation successful")

    def _validate_path(self, path: Any, config_key: str, must_exist: bool = False):
        """Validate a path from configuration.

        Args:
            path: Path to validate
            config_key: Configuration key name (for error messages)
            must_exist: Whether path must exist

        Raises:
            ValueError: If path is invalid

        """
        try:
            path_obj = Path(path)

            # Check for path traversal attempts
            resolved = path_obj.resolve()
            if ".." in str(path):
                logger.warning(f"Path {config_key} contains '..': {path}")

            # Check if must exist
            if must_exist and not resolved.exists():
                raise ValueError(f"{config_key} does not exist: {path}")

        except Exception as e:
            raise ValueError(f"Invalid path for {config_key}: {path} - {e}")

    def _validate_numeric_ranges(self):
        """Validate numeric configuration values are within reasonable ranges.

        Raises:
            ValueError: If any numeric value is out of range

        """
        llama_config = self.config.get("llama_cpp", {})

        # Validate context size
        ctx_size = llama_config.get("default_ctx_size", 8192)
        if not isinstance(ctx_size, int) or ctx_size < 512 or ctx_size > 128000:
            raise ValueError(
                f"Invalid default_ctx_size: {ctx_size}. "
                "Must be integer between 512 and 128000"
            )

        # Validate threads
        threads = llama_config.get("default_threads")
        if threads is not None:
            if not isinstance(threads, int) or threads < 1 or threads > 256:
                raise ValueError(
                    f"Invalid default_threads: {threads}. "
                    "Must be integer between 1 and 256, or None for auto"
                )

        # Validate GPU layers
        gpu_layers = llama_config.get("gpu_layers", 0)
        if not isinstance(gpu_layers, int) or gpu_layers < 0 or gpu_layers > 1000:
            raise ValueError(
                f"Invalid gpu_layers: {gpu_layers}. "
                "Must be non-negative integer (max 1000)"
            )

        # Validate port range
        advanced = self.config.get("advanced", {})
        port_start = advanced.get("port_range_start", 8080)
        port_end = advanced.get("port_range_end", 8180)

        if not isinstance(port_start, int) or port_start < 1024 or port_start > 65535:
            raise ValueError(
                f"Invalid port_range_start: {port_start}. "
                "Must be between 1024 and 65535"
            )

        if not isinstance(port_end, int) or port_end < port_start or port_end > 65535:
            raise ValueError(
                f"Invalid port_range_end: {port_end}. "
                "Must be between port_range_start and 65535"
            )

        # Validate memory limits
        limits = self.config.get("limits", {})
        max_memory = limits.get("max_memory_gb")
        if max_memory is not None:
            if not isinstance(max_memory, (int, float)) or max_memory < 1 or max_memory > 1024:
                raise ValueError(
                    f"Invalid max_memory_gb: {max_memory}. "
                    "Must be between 1 and 1024 GB"
                )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., "llama_cpp.server_path")
            default: Default value if key not found

        Returns:
            Configuration value or default

        """
        if not self._loaded:
            logger.warning("Configuration not loaded, call load() first")
            return default

        # Support dot notation for nested keys
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

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
        thresholds = self.config.get("thresholds", {})
        return thresholds.get(profile, {})

    def get_profile_config(self, profile_name: str) -> Dict[str, Any]:
        """Get complete configuration for a test profile.

        Args:
            profile_name: Name of the profile

        Returns:
            Dictionary containing profile configuration including thresholds

        """
        return {
            "thresholds": self.get_thresholds(profile_name),
            "test_data_path": self.config.get("test_data_path", "data/quality_tests.json")
        }

    def get_quants_for_mode(self, mode: Optional[str] = None) -> List[str]:
        """Get list of quantization levels to test for given mode.

        Args:
            mode: Test mode ("quick" or "full"), uses config if None

        Returns:
            List of quantization level strings

        """
        if mode is None:
            mode = self.config.get("test_mode", "full")

        if mode == "quick":
            return self.quick_mode_quants
        else:
            return self.full_mode_quants

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Dictionary with values to override

        Returns:
            Merged dictionary

        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

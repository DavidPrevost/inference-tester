"""Pytest configuration and shared fixtures.

This module provides fixtures and configuration for all tests.
"""

import pytest
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to temporary directory

    """
    return tmp_path


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Provide a sample configuration dictionary.

    Returns:
        Sample configuration

    """
    return {
        "llama_cpp": {
            "server_path": "/usr/local/bin/llama-server",
            "default_ctx_size": 8192,
            "default_threads": None
        },
        "test_mode": "full",
        "thresholds": {
            "interactive": {
                "min_tokens_per_sec": 2,
                "max_time_to_first_token": 30
            },
            "long_context": {
                "max_initial_load_time": 60
            },
            "batch": {
                "max_variance": 20
            }
        },
        "model_dir": "./models",
        "output": {
            "dir": "./results",
            "formats": ["json", "csv", "html"]
        }
    }


@pytest.fixture
def sample_models_config() -> list:
    """Provide a sample models configuration.

    Returns:
        List of model configurations

    """
    return [
        {
            "name": "Test-Model-3B",
            "size": "3B",
            "repo": "test/test-model-gguf",
            "files": {
                "Q4_K_M": "test-model-q4_k_m.gguf",
                "Q5_K_M": "test-model-q5_k_m.gguf"
            }
        }
    ]


@pytest.fixture
def mock_server_url():
    """Provide a mock server URL for testing.

    Returns:
        Mock server URL

    """
    return "http://localhost:8080"

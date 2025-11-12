"""Tests for ModelManager class."""

import pytest
from pathlib import Path
from model_manager import ModelManager


class TestModelManager:
    """Tests for model file management."""

    def test_initialization(self, tmp_path):
        """Test ModelManager initialization."""
        models_config = [
            {
                "name": "TestModel",
                "size_b": 7,
                "files": {
                    "Q4_K_M": "test-q4.gguf",
                    "Q5_K_M": "test-q5.gguf"
                }
            }
        ]

        mgr = ModelManager(tmp_path, models_config)

        assert mgr.model_dir == tmp_path
        assert len(mgr.models_config) == 1
        assert tmp_path.exists()  # Should create directory

    def test_scan_models_finds_files(self, tmp_path):
        """Test scanning for existing model files."""
        # Create test model files
        (tmp_path / "test-q4.gguf").touch()
        (tmp_path / "test-q5.gguf").touch()

        models_config = [
            {
                "name": "TestModel",
                "size_b": 7,
                "files": {
                    "Q4_K_M": "test-q4.gguf",
                    "Q5_K_M": "test-q5.gguf"
                }
            }
        ]

        mgr = ModelManager(tmp_path, models_config)
        mgr.scan_models()

        # Should find both models
        assert len(mgr.available_models) == 2
        assert ("TestModel", "Q4_K_M") in mgr.available_models
        assert ("TestModel", "Q5_K_M") in mgr.available_models

    def test_scan_models_handles_missing_files(self, tmp_path):
        """Test that scan handles missing model files gracefully."""
        # Don't create any files

        models_config = [
            {
                "name": "TestModel",
                "files": {
                    "Q4_K_M": "test-q4.gguf"
                }
            }
        ]

        mgr = ModelManager(tmp_path, models_config)
        mgr.scan_models()

        # Should find no models
        assert len(mgr.available_models) == 0

    def test_get_model_path(self, tmp_path):
        """Test getting path to specific model file."""
        model_file = tmp_path / "test-q4.gguf"
        model_file.touch()

        models_config = [
            {
                "name": "TestModel",
                "files": {
                    "Q4_K_M": "test-q4.gguf"
                }
            }
        ]

        mgr = ModelManager(tmp_path, models_config)
        mgr.scan_models()

        path = mgr.get_model_path("TestModel", "Q4_K_M")
        assert path == model_file
        assert path.exists()

    def test_get_model_path_returns_none_for_missing(self, tmp_path):
        """Test that get_model_path returns None for missing models."""
        mgr = ModelManager(tmp_path, [])
        mgr.scan_models()

        path = mgr.get_model_path("NonExistent", "Q4_K_M")
        assert path is None

    def test_estimate_memory(self, tmp_path):
        """Test memory estimation for models."""
        models_config = [
            {
                "name": "TestModel",
                "size_b": 7,  # 7B parameter model
                "files": {
                    "Q4_K_M": "test-q4.gguf"
                }
            }
        ]

        mgr = ModelManager(tmp_path, models_config)

        # Estimate memory for Q4_K_M quantization
        memory = mgr.estimate_memory("TestModel", "Q4_K_M")

        # Q4_K_M should use roughly 4.5 bits per param
        # 7B params * 4.5 bits = ~4GB + overhead
        assert 3.0 < memory < 6.0  # Rough range

    def test_get_model_definition(self, tmp_path):
        """Test retrieving model definition."""
        models_config = [
            {
                "name": "TestModel",
                "size_b": 7,
                "files": {
                    "Q4_K_M": "test-q4.gguf"
                }
            }
        ]

        mgr = ModelManager(tmp_path, models_config)

        model_def = mgr.get_model_definition("TestModel")

        assert model_def is not None
        assert model_def["name"] == "TestModel"
        assert model_def["size_b"] == 7

    def test_get_model_definition_returns_none_for_unknown(self, tmp_path):
        """Test that get_model_definition returns None for unknown models."""
        mgr = ModelManager(tmp_path, [])

        model_def = mgr.get_model_definition("NonExistent")
        assert model_def is None

    def test_list_available_models(self, tmp_path):
        """Test listing all available models."""
        (tmp_path / "test-q4.gguf").touch()

        models_config = [
            {
                "name": "TestModel",
                "files": {
                    "Q4_K_M": "test-q4.gguf"
                }
            }
        ]

        mgr = ModelManager(tmp_path, models_config)
        mgr.scan_models()

        available = mgr.list_available_models()

        assert len(available) == 1
        assert available[0] == ("TestModel", "Q4_K_M")

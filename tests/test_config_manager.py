"""Tests for ConfigManager class."""

import pytest
import tempfile
import yaml
from pathlib import Path
from config_manager import ConfigManager


class TestConfigManager:
    """Tests for configuration loading and validation."""

    def test_default_config_loads(self, tmp_path):
        """Test that default configuration loads correctly."""
        # Create minimal config files
        config_file = tmp_path / "config.yaml"
        models_file = tmp_path / "models.yaml"

        config_file.write_text(yaml.dump({
            "llama_cpp": {"server_path": "./llama-server"}
        }))

        models_file.write_text(yaml.dump({
            "models": [
                {
                    "name": "TestModel",
                    "files": {"Q4_K_M": "test-q4.gguf"}
                }
            ]
        }))

        config_mgr = ConfigManager(config_file, models_file)
        config_mgr.load()

        assert config_mgr.get("llama_cpp.server_path") == "./llama-server"
        assert config_mgr.get("test_mode") == "full"  # Default
        assert len(config_mgr.get_models()) == 1

    def test_missing_required_fields_raises_error(self, tmp_path):
        """Test that missing required config fields raises ValueError."""
        config_file = tmp_path / "config.yaml"
        models_file = tmp_path / "models.yaml"

        # Missing llama_cpp section
        config_file.write_text(yaml.dump({"test_mode": "quick"}))
        models_file.write_text(yaml.dump({"models": []}))

        config_mgr = ConfigManager(config_file, models_file)

        with pytest.raises(ValueError, match="llama_cpp"):
            config_mgr.load()

    def test_invalid_test_mode_raises_error(self, tmp_path):
        """Test that invalid test_mode raises ValueError."""
        config_file = tmp_path / "config.yaml"
        models_file = tmp_path / "models.yaml"

        config_file.write_text(yaml.dump({
            "llama_cpp": {"server_path": "./llama-server"},
            "test_mode": "invalid"
        }))
        models_file.write_text(yaml.dump({"models": []}))

        config_mgr = ConfigManager(config_file, models_file)

        with pytest.raises(ValueError, match="test_mode"):
            config_mgr.load()

    def test_get_with_dot_notation(self, tmp_path):
        """Test getting config values with dot notation."""
        config_file = tmp_path / "config.yaml"
        models_file = tmp_path / "models.yaml"

        config_file.write_text(yaml.dump({
            "llama_cpp": {
                "server_path": "./llama-server",
                "default_ctx_size": 4096
            }
        }))
        models_file.write_text(yaml.dump({"models": []}))

        config_mgr = ConfigManager(config_file, models_file)
        config_mgr.load()

        assert config_mgr.get("llama_cpp.server_path") == "./llama-server"
        assert config_mgr.get("llama_cpp.default_ctx_size") == 4096

    def test_get_profile_config(self, tmp_path):
        """Test getting profile configuration."""
        config_file = tmp_path / "config.yaml"
        models_file = tmp_path / "models.yaml"

        config_file.write_text(yaml.dump({
            "llama_cpp": {"server_path": "./llama-server"},
            "thresholds": {
                "interactive": {
                    "min_tokens_per_sec": 2.0
                }
            }
        }))
        models_file.write_text(yaml.dump({"models": []}))

        config_mgr = ConfigManager(config_file, models_file)
        config_mgr.load()

        profile_config = config_mgr.get_profile_config("interactive")

        assert "thresholds" in profile_config
        assert profile_config["thresholds"]["min_tokens_per_sec"] == 2.0

    def test_numeric_validation_context_size(self, tmp_path):
        """Test that invalid context sizes are rejected."""
        config_file = tmp_path / "config.yaml"
        models_file = tmp_path / "models.yaml"

        # Context size too small
        config_file.write_text(yaml.dump({
            "llama_cpp": {
                "server_path": "./llama-server",
                "default_ctx_size": 256  # Too small (< 512)
            }
        }))
        models_file.write_text(yaml.dump({"models": []}))

        config_mgr = ConfigManager(config_file, models_file)

        with pytest.raises(ValueError, match="default_ctx_size"):
            config_mgr.load()

    def test_numeric_validation_port_range(self, tmp_path):
        """Test that invalid port ranges are rejected."""
        config_file = tmp_path / "config.yaml"
        models_file = tmp_path / "models.yaml"

        # Invalid port range
        config_file.write_text(yaml.dump({
            "llama_cpp": {"server_path": "./llama-server"},
            "advanced": {
                "port_range_start": 100,  # Too low (< 1024)
                "port_range_end": 8180
            }
        }))
        models_file.write_text(yaml.dump({"models": []}))

        config_mgr = ConfigManager(config_file, models_file)

        with pytest.raises(ValueError, match="port_range_start"):
            config_mgr.load()

    def test_get_quants_for_mode(self, tmp_path):
        """Test getting quantization levels for different modes."""
        config_file = tmp_path / "config.yaml"
        models_file = tmp_path / "models.yaml"

        config_file.write_text(yaml.dump({
            "llama_cpp": {"server_path": "./llama-server"},
            "test_mode": "quick"
        }))

        models_file.write_text(yaml.dump({
            "models": [],
            "quick_mode_quants": ["Q4_K_M", "Q5_K_M"],
            "full_mode_quants": ["Q2_K", "Q3_K_M", "Q4_K_M", "Q5_K_M"]
        }))

        config_mgr = ConfigManager(config_file, models_file)
        config_mgr.load()

        # Quick mode quants
        quick_quants = config_mgr.get_quants_for_mode("quick")
        assert quick_quants == ["Q4_K_M", "Q5_K_M"]

        # Full mode quants
        full_quants = config_mgr.get_quants_for_mode("full")
        assert len(full_quants) == 4
        assert "Q2_K" in full_quants

"""Model management for LLM Inference Tester.

This module handles discovering, downloading, and managing GGUF model files.
It tracks which models are available locally and can download missing models
from HuggingFace.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Approximate memory multipliers for different quantization levels
# These are rough estimates: actual_memory ≈ file_size * multiplier
QUANT_MEMORY_MULTIPLIERS = {
    "Q2_K": 1.1,
    "Q3_K_M": 1.15,
    "Q4_K_M": 1.2,
    "Q4_K_S": 1.2,
    "Q5_K_M": 1.25,
    "Q5_K_S": 1.25,
    "Q6_K": 1.3,
    "Q8_0": 1.4,
    "F16": 1.5,
    "F32": 2.0
}

# Approximate bits per weight for quantization levels
QUANT_BITS = {
    "Q2_K": 2.5,
    "Q3_K_M": 3.5,
    "Q4_K_M": 4.5,
    "Q4_K_S": 4.0,
    "Q5_K_M": 5.5,
    "Q5_K_S": 5.0,
    "Q6_K": 6.5,
    "Q8_0": 8.5,
    "F16": 16.0,
    "F32": 32.0
}


class ModelManager:
    """Manages model file discovery, download, and metadata.

    Scans the model directory for existing GGUF files, matches them against
    model definitions, and downloads missing models as needed.
    """

    def __init__(self, model_dir: Path, models_config: List[Dict]):
        """Initialize the ModelManager.

        Args:
            model_dir: Directory containing model files
            models_config: List of model definitions from models.yaml

        """
        self.model_dir = Path(model_dir)
        self.models_config = models_config
        self.available_models: Dict[Tuple[str, str], Path] = {}  # (name, quant) -> path

        # Create model directory if it doesn't exist
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def scan_models(self):
        """Scan model directory for existing GGUF files.

        Updates the available_models dictionary with found models.
        """
        logger.info("Scanning for models in %s", self.model_dir)

        self.available_models.clear()

        # Scan for all .gguf files
        if not self.model_dir.exists():
            logger.warning("Model directory %s does not exist", self.model_dir)
            return

        gguf_files = list(self.model_dir.rglob("*.gguf"))
        logger.debug("Found %d GGUF files", len(gguf_files))

        # Match found files against model definitions
        for model_def in self.models_config:
            model_name = model_def["name"]
            files = model_def.get("files", {})

            for quant, filename in files.items():
                # Look for this specific file
                for gguf_path in gguf_files:
                    if gguf_path.name == filename:
                        self.available_models[(model_name, quant)] = gguf_path
                        logger.debug("Found %s (%s) at %s", model_name, quant, gguf_path)
                        break

        logger.info("Found %d configured models locally", len(self.available_models))

    def get_model_path(self, model_name: str, quant: str) -> Optional[Path]:
        """Get path to a specific model file.

        Args:
            model_name: Model name (e.g., "Llama-3.2-7B-Instruct")
            quant: Quantization level (e.g., "Q4_K_M")

        Returns:
            Path to model file, or None if not found

        """
        key = (model_name, quant)
        return self.available_models.get(key)

    def download_model(self, model_name: str, quant: str) -> Path:
        """Download a model from HuggingFace.

        Args:
            model_name: Model name
            quant: Quantization level

        Returns:
            Path to downloaded model file

        Raises:
            ValueError: If model definition not found
            RuntimeError: If download fails

        """
        logger.info("Downloading %s (%s)", model_name, quant)

        # Find model definition
        model_def = None
        for m in self.models_config:
            if m["name"] == model_name:
                model_def = m
                break

        if not model_def:
            raise ValueError(f"Model {model_name} not found in configuration")

        # Get filename for this quantization
        files = model_def.get("files", {})
        if quant not in files:
            raise ValueError(f"Quantization {quant} not available for {model_name}")

        filename = files[quant]
        repo = model_def["repo"]

        # Determine size category for subdirectory
        size = model_def.get("size", "unknown")
        target_dir = self.model_dir / size
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        # Check if already downloaded
        if target_path.exists():
            logger.info("Model already exists at %s", target_path)
            self.available_models[(model_name, quant)] = target_path
            return target_path

        # Download from HuggingFace
        try:
            from huggingface_hub import hf_hub_download
            from tqdm import tqdm

            logger.info("Downloading from HuggingFace: %s/%s", repo, filename)

            downloaded_path = hf_hub_download(
                repo_id=repo,
                filename=filename,
                cache_dir=None,  # Use default cache
                local_dir=str(target_dir),
                local_dir_use_symlinks=False
            )

            final_path = Path(downloaded_path)

            # Update available models
            self.available_models[(model_name, quant)] = final_path

            logger.info("Successfully downloaded to %s", final_path)
            return final_path

        except ImportError:
            raise RuntimeError(
                "huggingface_hub not available. Install with: pip install huggingface-hub"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to download model: {e}")

    def ensure_model(self, model_name: str, quant: str) -> Path:
        """Ensure a model is available, downloading if necessary.

        Args:
            model_name: Model name
            quant: Quantization level

        Returns:
            Path to model file

        Raises:
            ValueError: If model definition not found
            RuntimeError: If download fails

        """
        path = self.get_model_path(model_name, quant)
        if path and path.exists():
            logger.debug("Model %s (%s) already available at %s", model_name, quant, path)
            return path

        logger.info("Model %s (%s) not found locally, downloading...", model_name, quant)
        return self.download_model(model_name, quant)

    def estimate_memory(self, model_name: str, quant: str) -> float:
        """Estimate memory requirement for a model.

        Args:
            model_name: Model name
            quant: Quantization level

        Returns:
            Estimated memory in GB

        """
        # Find model definition
        model_def = None
        for m in self.models_config:
            if m["name"] == model_name:
                model_def = m
                break

        if not model_def:
            logger.warning("Model %s not found, cannot estimate memory", model_name)
            return 0.0

        # Try to get actual file size if available
        path = self.get_model_path(model_name, quant)
        if path and path.exists():
            file_size_gb = path.stat().st_size / (1024**3)
            multiplier = QUANT_MEMORY_MULTIPLIERS.get(quant, 1.3)
            estimated = file_size_gb * multiplier
            logger.debug(
                "Memory estimate for %s (%s): %.2f GB (file: %.2f GB, multiplier: %.2f)",
                model_name, quant, estimated, file_size_gb, multiplier
            )
            return estimated

        # Estimate based on model size and quant level
        size_str = model_def.get("size", "7B")

        # Parse size (e.g., "7B" -> 7, "1.5B" -> 1.5)
        try:
            if "B" in size_str:
                params_b = float(size_str.replace("B", ""))
            else:
                params_b = 7.0  # Default
        except ValueError:
            params_b = 7.0

        # Estimate: params (in billions) * bits_per_weight / 8 (to get GB)
        bits = QUANT_BITS.get(quant, 4.5)
        file_size_estimate = (params_b * bits) / 8.0

        # Add overhead multiplier
        multiplier = QUANT_MEMORY_MULTIPLIERS.get(quant, 1.3)
        estimated = file_size_estimate * multiplier

        logger.debug(
            "Memory estimate for %s (%s): %.2f GB (params: %.1fB, bits: %.1f)",
            model_name, quant, estimated, params_b, bits
        )

        return estimated

    def get_model_metadata(self, model_name: str, quant: str) -> Dict[str, Any]:
        """Get metadata for a specific model.

        Args:
            model_name: Model name
            quant: Quantization level

        Returns:
            Dictionary containing model metadata

        """
        # Find model definition
        model_def = None
        for m in self.models_config:
            if m["name"] == model_name:
                model_def = m
                break

        if not model_def:
            return {}

        metadata = {
            "name": model_name,
            "size": model_def.get("size", "unknown"),
            "repo": model_def.get("repo", ""),
            "quant": quant,
            "estimated_memory_gb": self.estimate_memory(model_name, quant)
        }

        # Add optional metadata if present
        if "metadata" in model_def:
            metadata.update(model_def["metadata"])

        # Add file info if available
        path = self.get_model_path(model_name, quant)
        if path and path.exists():
            metadata["file_path"] = str(path)
            metadata["file_size_gb"] = path.stat().st_size / (1024**3)
            metadata["available"] = True
        else:
            metadata["available"] = False

        return metadata

    def get_model_definition(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get the full model definition from config.

        Args:
            model_name: Model name

        Returns:
            Model definition dictionary, or None if not found

        """
        for model_def in self.models_config:
            if model_def["name"] == model_name:
                return model_def
        return None

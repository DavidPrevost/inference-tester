"""Automatic model downloader from Hugging Face.

This module handles downloading GGUF model files from Hugging Face Hub
automatically when they're not found locally.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)


class ModelDownloader:
    """Downloads GGUF models from Hugging Face Hub."""

    def __init__(self, model_dir: Path):
        """Initialize the downloader.

        Args:
            model_dir: Directory to download models into
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def check_missing_models(self, models_config: List[Dict]) -> List[Dict]:
        """Check which configured models are missing locally.

        Args:
            models_config: List of model configurations

        Returns:
            List of missing model entries with download info
        """
        missing = []

        for model_def in models_config:
            model_name = model_def["name"]
            repo = model_def.get("repo")
            files = model_def.get("files", {})

            if not repo:
                logger.debug(f"No repo specified for {model_name}, skipping download check")
                continue

            for quant, filename in files.items():
                file_path = self.model_dir / filename

                if not file_path.exists():
                    missing.append({
                        "model_name": model_name,
                        "quant": quant,
                        "filename": filename,
                        "repo": repo,
                        "path": file_path
                    })
                    logger.debug(f"Missing: {model_name} ({quant})")

        return missing

    def download_model(
        self,
        repo_id: str,
        filename: str,
        local_path: Path,
        show_progress: bool = True
    ) -> bool:
        """Download a single model file from Hugging Face.

        Args:
            repo_id: Hugging Face repository ID (e.g., "bartowski/Llama-3.2-3B-Instruct-GGUF")
            filename: Filename in the repo
            local_path: Local path to save to
            show_progress: Whether to show download progress

        Returns:
            True if successful, False otherwise
        """
        try:
            from huggingface_hub import hf_hub_download
            from huggingface_hub.utils import HfHubHTTPError
        except ImportError:
            logger.error(
                "huggingface_hub library not installed. "
                "Install with: pip install huggingface-hub"
            )
            return False

        try:
            logger.info(f"Downloading {filename} from {repo_id}...")
            logger.info(f"This may take several minutes depending on file size and connection speed.")

            # Download to temp location first
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=self.model_dir,
                local_dir_use_symlinks=False,
                resume_download=True
            )

            logger.info(f"Successfully downloaded: {filename}")
            return True

        except HfHubHTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Model file not found: {repo_id}/{filename}")
                logger.error("This file may have been renamed or removed from Hugging Face")
            else:
                logger.error(f"HTTP error downloading model: {e}")
            return False

        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            return False

    def download_missing_models(
        self,
        missing_models: List[Dict],
        prompt_user: bool = True
    ) -> Dict[str, bool]:
        """Download all missing models.

        Args:
            missing_models: List of missing model info dicts
            prompt_user: Whether to prompt before downloading

        Returns:
            Dict mapping model keys to success status
        """
        if not missing_models:
            logger.info("All configured models are present locally")
            return {}

        # Calculate total download size estimate
        logger.info("=" * 60)
        logger.info(f"Found {len(missing_models)} missing model files")
        logger.info("=" * 60)

        for item in missing_models:
            logger.info(f"  • {item['model_name']} ({item['quant']})")

        logger.info("")
        logger.info("These files will be downloaded from Hugging Face")

        # Estimate sizes
        size_estimates = {
            "Q2_K": "~1-4 GB per model",
            "Q3_K_M": "~1.5-5 GB per model",
            "Q4_K_M": "~2-6 GB per model",
            "Q5_K_M": "~2.5-7 GB per model",
            "Q6_K": "~3-8 GB per model",
            "Q8_0": "~4-10 GB per model",
        }

        # Show size estimates
        total_estimate_low = len(missing_models) * 2  # GB
        total_estimate_high = len(missing_models) * 6  # GB
        logger.info(f"Estimated total download: {total_estimate_low}-{total_estimate_high} GB")
        logger.info("=" * 60)
        logger.info("")

        if prompt_user:
            response = input("Download missing models now? (yes/no): ").strip().lower()
            if response not in ["yes", "y"]:
                logger.info("Skipping model downloads")
                return {}

        # Download each model
        results = {}
        for i, item in enumerate(missing_models, 1):
            key = f"{item['model_name']}_{item['quant']}"
            logger.info(f"\n[{i}/{len(missing_models)}] Downloading {item['model_name']} ({item['quant']})...")

            success = self.download_model(
                repo_id=item["repo"],
                filename=item["filename"],
                local_path=item["path"]
            )

            results[key] = success

            if not success:
                logger.warning(f"Failed to download {item['filename']}")
                logger.warning("Tests using this model will be skipped")

        # Summary
        successful = sum(1 for v in results.values() if v)
        failed = len(results) - successful

        logger.info("")
        logger.info("=" * 60)
        logger.info("Download Summary")
        logger.info("=" * 60)
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info("=" * 60)

        return results

    def download_specific_model(
        self,
        model_name: str,
        quant: str,
        models_config: List[Dict]
    ) -> bool:
        """Download a specific model by name and quantization.

        Args:
            model_name: Model name
            quant: Quantization level
            models_config: List of model configurations

        Returns:
            True if successful, False otherwise
        """
        # Find model definition
        model_def = None
        for m in models_config:
            if m["name"] == model_name:
                model_def = m
                break

        if not model_def:
            logger.error(f"Model {model_name} not found in configuration")
            return False

        repo = model_def.get("repo")
        if not repo:
            logger.error(f"No repository specified for {model_name}")
            return False

        files = model_def.get("files", {})
        if quant not in files:
            logger.error(f"Quantization {quant} not available for {model_name}")
            return False

        filename = files[quant]
        local_path = self.model_dir / filename

        if local_path.exists():
            logger.info(f"Model already exists: {filename}")
            return True

        return self.download_model(repo, filename, local_path)


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes.

    Args:
        file_path: Path to file

    Returns:
        Size in MB
    """
    if not file_path.exists():
        return 0.0
    return file_path.stat().st_size / (1024 * 1024)

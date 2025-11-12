"""Matrix runner for orchestrating comprehensive model testing.

This module implements smart testing across multiple models and quantization
levels, with intelligent early termination to save time.
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config_manager import ConfigManager
from model_manager import ModelManager
from server_manager import ServerManager
from test_profiles import get_profile
from utils.hardware import get_available_memory

logger = logging.getLogger(__name__)


@dataclass
class TestConfiguration:
    """Represents a single test configuration (model + quant + profile)."""
    model_name: str
    quant: str
    profile_name: str
    estimated_memory_gb: float
    skipped: bool = False
    skip_reason: Optional[str] = None


@dataclass
class TestRun:
    """Results from a single test run."""
    model_name: str
    quant: str
    profile_name: str
    status: str  # excellent, good, acceptable, poor, failed, error, skipped
    passed: bool
    metrics: Dict[str, Any]
    interpretation: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    timestamp: Optional[str] = None


class MatrixRunner:
    """Orchestrates testing across multiple models and profiles.

    Implements smart termination strategies to avoid wasting time on
    configurations that are unlikely to work.
    """

    def __init__(
        self,
        config_mgr: ConfigManager,
        model_mgr: ModelManager,
        server_mgr: ServerManager
    ):
        """Initialize the matrix runner.

        Args:
            config_mgr: Configuration manager
            model_mgr: Model manager
            server_mgr: Server manager
        """
        self.config_mgr = config_mgr
        self.model_mgr = model_mgr
        self.server_mgr = server_mgr

        # Results tracking
        self.test_runs: List[TestRun] = []
        self.failed_models: Dict[Tuple[str, str], str] = {}  # (name, quant) -> reason

        # Memory tracking for trend analysis
        self.memory_observations: List[Dict[str, Any]] = []

        # Checkpoint file for resume capability
        self.checkpoint_file: Optional[Path] = None

    def run_matrix(
        self,
        models: Optional[List[str]] = None,
        quants: Optional[List[str]] = None,
        profiles: Optional[List[str]] = None,
        checkpoint_path: Optional[str] = None
    ) -> List[TestRun]:
        """Run the full testing matrix.

        Args:
            models: List of model names to test (None = all from config)
            quants: List of quantization levels (None = from test mode)
            profiles: List of profile names (None = all)
            checkpoint_path: Path to checkpoint file for resume

        Returns:
            List of test runs with results
        """
        logger.info("Starting matrix test run")

        # Setup checkpoint
        if checkpoint_path:
            self.checkpoint_file = Path(checkpoint_path)
            self._load_checkpoint()

        # Determine test matrix
        test_configs = self._build_test_matrix(models, quants, profiles)

        logger.info(f"Generated {len(test_configs)} test configurations")

        # Execute tests
        for i, config in enumerate(test_configs):
            # Check for graceful shutdown request
            from shutdown import is_shutdown_requested
            if is_shutdown_requested():
                logger.info("\n=== Shutdown requested - saving progress and exiting ===")
                if self.checkpoint_file:
                    self._save_checkpoint()
                logger.info(f"Progress saved. Completed {len(self.test_runs)} tests.")
                break

            logger.info(
                f"\n=== Test {i+1}/{len(test_configs)}: "
                f"{config.model_name} {config.quant} - {config.profile_name} ==="
            )

            # Check if already tested (from checkpoint)
            if self._is_already_tested(config):
                logger.info("Already tested, skipping...")
                continue

            # Run test
            test_run = self._execute_test(config)
            self.test_runs.append(test_run)

            # Save checkpoint
            if self.checkpoint_file:
                self._save_checkpoint()

            # Check if we should skip remaining tests for this model/quant
            if test_run.status == "failed" and not config.skipped:
                self._analyze_failure(config, test_run)

        logger.info("\n=== Matrix testing complete ===")
        logger.info(f"Total tests: {len(self.test_runs)}")
        logger.info(f"Passed: {sum(1 for r in self.test_runs if r.passed)}")
        logger.info(f"Failed: {sum(1 for r in self.test_runs if not r.passed)}")

        return self.test_runs

    def _build_test_matrix(
        self,
        models: Optional[List[str]],
        quants: Optional[List[str]],
        profiles: Optional[List[str]]
    ) -> List[TestConfiguration]:
        """Build the test configuration matrix.

        Args:
            models: Model names
            quants: Quantization levels
            profiles: Profile names

        Returns:
            List of test configurations
        """
        # Get models from config if not specified
        if models is None:
            all_models = self.config_mgr.get_models()
            models = [m["name"] for m in all_models]

        # Get quants from test mode if not specified
        if quants is None:
            test_mode = self.config_mgr.get("test_mode", "full")
            quants = self.config_mgr.get_quants_for_mode(test_mode)

        # Get profiles from config if not specified
        if profiles is None:
            from test_profiles import list_profiles
            profiles = list_profiles()

        # Build configurations in priority order (Q4_K_M first)
        configs = []

        # Priority order for quantization levels
        quant_priority = ["Q4_K_M", "Q5_K_M", "Q6_K", "Q3_K_M", "Q2_K", "Q8_0"]
        ordered_quants = [q for q in quant_priority if q in quants]
        ordered_quants.extend([q for q in quants if q not in quant_priority])

        # For each quant level, test all models
        for quant in ordered_quants:
            for model_name in models:
                # Check if this model supports this quant
                model_def = self.model_mgr.get_model_definition(model_name)
                if not model_def:
                    continue

                files = model_def.get("files", {})
                if quant not in files:
                    continue

                # Estimate memory
                estimated_memory = self.model_mgr.estimate_memory(model_name, quant)

                # Create test configs for each profile
                for profile_name in profiles:
                    # Skip stress test for now (will add separately)
                    if profile_name == "stress":
                        continue

                    config = TestConfiguration(
                        model_name=model_name,
                        quant=quant,
                        profile_name=profile_name,
                        estimated_memory_gb=estimated_memory
                    )

                    # Apply early termination checks
                    self._apply_smart_termination(config)

                    configs.append(config)

        # Add stress tests at the end (using best performing configs)
        # This will be added after benchmark tests complete

        return configs

    def _apply_smart_termination(self, config: TestConfiguration):
        """Apply smart termination logic to a config.

        Modifies config in place to mark as skipped if appropriate.

        Args:
            config: Test configuration to check
        """
        model_key = (config.model_name, config.quant)

        # Strategy 1: Pre-flight memory check
        available_memory = get_available_memory()
        if config.estimated_memory_gb > available_memory * 0.9:
            config.skipped = True
            config.skip_reason = (
                f"Insufficient memory: need {config.estimated_memory_gb:.1f}GB, "
                f"available {available_memory:.1f}GB"
            )
            logger.warning(f"SKIP: {config.skip_reason}")
            return

        # Strategy 2: Check if this model/quant already failed loading
        if model_key in self.failed_models:
            config.skipped = True
            config.skip_reason = f"Model failed earlier: {self.failed_models[model_key]}"
            logger.info(f"SKIP: {config.skip_reason}")
            return

        # Strategy 3: Performance threshold termination
        # Check if larger models at same quant already failed
        model_def = self.model_mgr.get_model_definition(config.model_name)
        if model_def:
            model_size = model_def.get("size", "")
            # Parse size (e.g., "7B" -> 7)
            try:
                if "B" in model_size:
                    size_num = float(model_size.replace("B", ""))

                    # Check if any smaller model at this quant failed
                    for (failed_name, failed_quant), reason in self.failed_models.items():
                        if failed_quant == config.quant:
                            failed_def = self.model_mgr.get_model_definition(failed_name)
                            if failed_def:
                                failed_size = failed_def.get("size", "")
                                if "B" in failed_size:
                                    failed_num = float(failed_size.replace("B", ""))
                                    if failed_num < size_num:
                                        config.skipped = True
                                        config.skip_reason = (
                                            f"Smaller model ({failed_name}) failed at {config.quant}, "
                                            f"larger model unlikely to work"
                                        )
                                        logger.info(f"SKIP: {config.skip_reason}")
                                        return
            except (ValueError, AttributeError):
                pass

        # Strategy 5: Memory trend analysis
        if len(self.memory_observations) >= 3:
            # Predict if this config will exceed memory
            predicted_memory = self._predict_memory_usage(config.model_name, config.quant)
            if predicted_memory and predicted_memory > available_memory * 0.95:
                config.skipped = True
                config.skip_reason = (
                    f"Predicted memory usage {predicted_memory:.1f}GB "
                    f"exceeds available {available_memory:.1f}GB"
                )
                logger.info(f"SKIP: {config.skip_reason}")
                return

    def _predict_memory_usage(
        self,
        model_name: str,
        quant: str
    ) -> Optional[float]:
        """Predict memory usage based on observed trends.

        Args:
            model_name: Model name
            quant: Quantization level

        Returns:
            Predicted memory in GB, or None if not enough data
        """
        # Simple prediction based on similar models
        # In production, could use linear regression

        similar_observations = []
        for obs in self.memory_observations:
            if obs["quant"] == quant:
                similar_observations.append(obs)

        if not similar_observations:
            return None

        # Use average of similar observations
        avg_memory = sum(o["memory_gb"] for o in similar_observations) / len(similar_observations)

        # Apply scaling factor based on estimated memory
        estimated = self.model_mgr.estimate_memory(model_name, quant)
        if similar_observations:
            avg_estimated = sum(
                self.model_mgr.estimate_memory(o["model_name"], o["quant"])
                for o in similar_observations
            ) / len(similar_observations)

            if avg_estimated > 0:
                scale = estimated / avg_estimated
                return avg_memory * scale

        return None

    def _execute_test(self, config: TestConfiguration) -> TestRun:
        """Execute a single test configuration.

        Args:
            config: Test configuration

        Returns:
            Test run result
        """
        start_time = time.time()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Handle skipped tests
        if config.skipped:
            return TestRun(
                model_name=config.model_name,
                quant=config.quant,
                profile_name=config.profile_name,
                status="skipped",
                passed=False,
                metrics={},
                error=config.skip_reason,
                duration_seconds=0,
                timestamp=timestamp
            )

        connection = None
        try:
            # Ensure model is available
            logger.info(f"Ensuring model {config.model_name} ({config.quant}) is available...")
            model_path = self.model_mgr.ensure_model(config.model_name, config.quant)

            # Get context size for this profile
            profile = get_profile(config.profile_name)
            ctx_size = profile.get_required_context_size()

            # Start server
            logger.info(f"Starting llama.cpp server (ctx_size={ctx_size})...")
            connection = self.server_mgr.start(
                model_path=model_path,
                ctx_size=ctx_size
            )

            if not connection:
                raise RuntimeError("Failed to start server")

            # Record memory usage
            from utils.hardware import get_memory_usage
            mem_used, _, _ = get_memory_usage()
            self.memory_observations.append({
                "model_name": config.model_name,
                "quant": config.quant,
                "memory_gb": mem_used,
                "estimated_gb": config.estimated_memory_gb
            })

            # Run the test profile
            logger.info(f"Running {config.profile_name} profile...")
            profile_config = self.config_mgr.get_profile_config(config.profile_name)
            result = profile.run(connection.url, profile_config)

            duration = time.time() - start_time

            return TestRun(
                model_name=config.model_name,
                quant=config.quant,
                profile_name=config.profile_name,
                status=result.status,
                passed=result.passed,
                metrics=result.metrics,
                interpretation=result.interpretation,
                error=result.error,
                duration_seconds=duration,
                timestamp=timestamp
            )

        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)

            duration = time.time() - start_time

            # Mark this model/quant as failed
            model_key = (config.model_name, config.quant)
            self.failed_models[model_key] = str(e)

            return TestRun(
                model_name=config.model_name,
                quant=config.quant,
                profile_name=config.profile_name,
                status="error",
                passed=False,
                metrics={},
                error=str(e),
                duration_seconds=duration,
                timestamp=timestamp
            )

        finally:
            # Always stop server if it was started
            if connection is not None:
                try:
                    logger.info("Stopping server...")
                    self.server_mgr.stop()
                except Exception as e:
                    logger.warning(f"Error stopping server: {e}")

    def _analyze_failure(self, config: TestConfiguration, test_run: TestRun):
        """Analyze a test failure to inform future skipping decisions.

        Args:
            config: Test configuration that failed
            test_run: Test run result
        """
        # If performance is extremely poor, mark the model/quant as failed
        metrics = test_run.metrics

        # Check critical thresholds
        ttft = metrics.get("time_to_first_token", 0)
        tps = metrics.get("tokens_per_sec", 0)

        if ttft > 60 or tps < 1:
            model_key = (config.model_name, config.quant)
            self.failed_models[model_key] = (
                f"Performance too poor: TTFT={ttft:.1f}s, TPS={tps:.2f}"
            )
            logger.warning(f"Marking {model_key} as failed for future tests")

    def _is_already_tested(self, config: TestConfiguration) -> bool:
        """Check if a configuration was already tested.

        Args:
            config: Test configuration

        Returns:
            True if already tested
        """
        for run in self.test_runs:
            if (run.model_name == config.model_name and
                run.quant == config.quant and
                run.profile_name == config.profile_name):
                return True
        return False

    def _save_checkpoint(self):
        """Save current progress to checkpoint file."""
        if not self.checkpoint_file:
            return

        checkpoint_data = {
            "test_runs": [asdict(run) for run in self.test_runs],
            "failed_models": {
                f"{k[0]}_{k[1]}": v for k, v in self.failed_models.items()
            },
            "memory_observations": self.memory_observations
        }

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.debug(f"Checkpoint saved to {self.checkpoint_file}")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self):
        """Load progress from checkpoint file."""
        if not self.checkpoint_file or not self.checkpoint_file.exists():
            return

        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)

            # Restore test runs
            self.test_runs = [
                TestRun(**run_data) for run_data in checkpoint_data.get("test_runs", [])
            ]

            # Restore failed models
            failed_models_dict = checkpoint_data.get("failed_models", {})
            self.failed_models = {
                tuple(k.split("_", 1)): v for k, v in failed_models_dict.items()
            }

            # Restore memory observations
            self.memory_observations = checkpoint_data.get("memory_observations", [])

            logger.info(f"Loaded checkpoint: {len(self.test_runs)} tests already completed")

        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")

    def get_results_summary(self) -> Dict[str, Any]:
        """Get summary of all test results.

        Returns:
            Dictionary with summary statistics
        """
        total = len(self.test_runs)
        passed = sum(1 for r in self.test_runs if r.passed)
        failed = sum(1 for r in self.test_runs if not r.passed and r.status != "skipped")
        skipped = sum(1 for r in self.test_runs if r.status == "skipped")

        # Group by status
        by_status = {}
        for run in self.test_runs:
            status = run.status
            by_status[status] = by_status.get(status, 0) + 1

        # Find best configurations
        excellent_runs = [r for r in self.test_runs if r.status == "excellent"]
        good_runs = [r for r in self.test_runs if r.status == "good"]

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "by_status": by_status,
            "excellent_configs": len(excellent_runs),
            "good_configs": len(good_runs),
            "best_configs": [
                {
                    "model": r.model_name,
                    "quant": r.quant,
                    "profile": r.profile_name,
                    "status": r.status
                }
                for r in excellent_runs[:5]  # Top 5
            ]
        }

"""CLI entry point for LLM Inference Tester.

This module provides the command-line interface for running inference tests
on LLM models. It orchestrates the testing process from configuration loading
through model testing to report generation.
"""

import argparse
import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Path = None):
    """Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file

    """
    handlers = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers
    )

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def parse_args():
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace

    """
    parser = argparse.ArgumentParser(
        description="Test practical performance limits of LLMs on edge devices",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --quick                    # Quick test (Q4/Q5 only, ~1 hour)
  %(prog)s --full                     # Full test (all quants, ~2-4 hours)
  %(prog)s --models "Llama-3.2-7B"    # Test specific model
  %(prog)s --profiles interactive,batch  # Test specific profiles
  %(prog)s --resume results/checkpoint.json  # Resume interrupted test
        """
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to configuration file (default: config.yaml)"
    )

    parser.add_argument(
        "--models-config",
        type=Path,
        default=Path("models.yaml"),
        help="Path to models configuration (default: models.yaml)"
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--quick",
        action="store_true",
        help="Quick test mode (Q4/Q5 only, ~1 hour)"
    )
    mode_group.add_argument(
        "--full",
        action="store_true",
        help="Full test mode (all quants, ~2-4 hours)"
    )

    parser.add_argument(
        "--models",
        type=str,
        help="Comma-separated list of model names to test"
    )

    parser.add_argument(
        "--quants",
        type=str,
        help="Comma-separated list of quantizations to test (e.g., Q4_K_M,Q5_K_M)"
    )

    parser.add_argument(
        "--profiles",
        type=str,
        help="Comma-separated list of test profiles to run"
    )

    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Skip quality/accuracy tests"
    )

    parser.add_argument(
        "--skip-stress",
        action="store_true",
        help="Skip stress tests"
    )

    parser.add_argument(
        "--resume",
        type=Path,
        help="Resume from checkpoint file"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for results (overrides config)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be tested without running tests"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    args = parse_args()

    # Set up logging
    log_file = Path("inference-tester.log")
    setup_logging(level=args.log_level, log_file=log_file)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("LLM Inference Tester v0.1.0")
    logger.info("=" * 60)

    try:
        # Import required modules
        from config_manager import ConfigManager
        from model_manager import ModelManager
        from server_manager import ServerManager
        from test_profiles import get_profile

        # Load configuration
        logger.info("Loading configuration...")
        config_mgr = ConfigManager(args.config, args.models_config)
        config_mgr.load()

        logger.info("Configuration loaded successfully")
        logger.info("Test mode: %s", config_mgr.get("test_mode"))

        # Override test mode if specified
        if args.quick:
            config_mgr.config["test_mode"] = "quick"
            logger.info("Mode: Quick test (~1 hour)")
        elif args.full:
            config_mgr.config["test_mode"] = "full"
            logger.info("Mode: Full test (~2-4 hours)")

        # Initialize managers
        model_dir = Path(config_mgr.get("model_dir"))
        model_mgr = ModelManager(model_dir, config_mgr.get_models())

        # Scan for existing models
        logger.info("Scanning for models...")
        model_mgr.scan_models()

        # Get server configuration
        server_path = Path(config_mgr.get("llama_cpp.server_path"))
        ctx_size = config_mgr.get("llama_cpp.default_ctx_size")
        server_mgr = ServerManager(server_path, default_ctx_size=ctx_size)

        # For Phase 2 proof of concept: Test with first available model
        # In future phases, this will iterate through the test matrix
        models = config_mgr.get_models()
        if not models:
            logger.error("No models defined in configuration")
            return 1

        # Use first model at Q4_K_M (common sweet spot)
        test_model = models[0]
        test_quant = "Q4_K_M"

        logger.info("=" * 60)
        logger.info("Phase 2 Proof of Concept Test")
        logger.info("Model: %s", test_model["name"])
        logger.info("Quantization: %s", test_quant)
        logger.info("=" * 60)

        # Ensure model is available
        logger.info("Ensuring model is available...")
        try:
            model_path = model_mgr.ensure_model(test_model["name"], test_quant)
            logger.info("Model ready at: %s", model_path)
        except Exception as e:
            logger.error("Failed to get model: %s", e)
            logger.info("This is expected if the model hasn't been downloaded yet.")
            logger.info("In a full implementation, the tool would download it automatically.")
            return 1

        # Start server
        logger.info("Starting llama.cpp server...")
        try:
            connection = server_mgr.start(model_path)
            logger.info("Server started at: %s", connection.url)

            # Run interactive profile test
            logger.info("Running interactive test profile...")
            profile = get_profile("interactive")

            # Get profile config
            profile_config = {
                "thresholds": config_mgr.get_thresholds("interactive")
            }

            # Run test
            result = profile.run(connection.url, profile_config)

            # Display results
            logger.info("=" * 60)
            logger.info("TEST RESULTS")
            logger.info("=" * 60)
            logger.info("Profile: %s", result.profile)
            logger.info("Status: %s", result.status)
            logger.info("Passed: %s", result.passed)
            logger.info("")
            logger.info("Metrics:")
            for key, value in result.metrics.items():
                logger.info("  %s: %.2f", key, value)

            if result.interpretation:
                logger.info("")
                logger.info("Interpretations:")
                for key, interp in result.interpretation.items():
                    logger.info("  %s: %s", key, interp)

            logger.info("=" * 60)

            if result.passed:
                logger.info("✓ Test PASSED")
                return_code = 0
            else:
                logger.warning("✗ Test FAILED")
                return_code = 1

        finally:
            # Always stop the server
            logger.info("Stopping server...")
            server_mgr.stop()
            logger.info("Server stopped")

        logger.info("")
        logger.info("Phase 2 proof of concept complete!")
        logger.info("Next: Implement full matrix testing and all profiles")

        return return_code

    except FileNotFoundError as e:
        logger.error("Configuration error: %s", e)
        logger.error("Please ensure config.yaml and models.yaml exist")
        logger.error("You can copy config.example.yaml and models.example.yaml to get started")
        return 1

    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

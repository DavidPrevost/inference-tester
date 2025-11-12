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

        # Parse model/quant/profile filters
        models = args.models.split(",") if args.models else None
        quants = args.quants.split(",") if args.quants else None
        profiles = args.profiles.split(",") if args.profiles else None

        # Handle skip flags
        if args.skip_quality and profiles:
            profiles = [p for p in profiles if p != "quality"]
        if args.skip_stress and profiles:
            profiles = [p for p in profiles if p != "stress"]

        # Dry run: show what would be tested
        if args.dry_run:
            logger.info("=" * 60)
            logger.info("DRY RUN - No tests will be executed")
            logger.info("=" * 60)
            from matrix_runner import MatrixRunner
            runner = MatrixRunner(config_mgr, model_mgr, server_mgr)
            test_configs = runner._build_test_matrix(models, quants, profiles)

            logger.info(f"Would run {len(test_configs)} test configurations:")
            for i, config in enumerate(test_configs[:20]):  # Show first 20
                logger.info(
                    f"  {i+1}. {config.model_name} {config.quant} - {config.profile_name}"
                )
            if len(test_configs) > 20:
                logger.info(f"  ... and {len(test_configs) - 20} more")
            return 0

        # Initialize matrix runner
        logger.info("=" * 60)
        logger.info("Starting Matrix Test Run")
        logger.info("=" * 60)

        from matrix_runner import MatrixRunner
        runner = MatrixRunner(config_mgr, model_mgr, server_mgr)

        # Setup checkpoint path
        checkpoint_path = args.resume
        if not checkpoint_path and args.output_dir:
            checkpoint_path = args.output_dir / "checkpoint.json"

        # Run the matrix
        test_runs = runner.run_matrix(
            models=models,
            quants=quants,
            profiles=profiles,
            checkpoint_path=str(checkpoint_path) if checkpoint_path else None
        )

        # Get summary
        summary = runner.get_results_summary()

        # Display results
        logger.info("\n" + "=" * 60)
        logger.info("MATRIX TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total tests: {summary['total_tests']}")
        logger.info(f"Passed: {summary['passed']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Skipped: {summary['skipped']}")
        logger.info("")
        logger.info("Results by status:")
        for status, count in summary['by_status'].items():
            logger.info(f"  {status}: {count}")

        if summary['best_configs']:
            logger.info("")
            logger.info("Best performing configurations:")
            for config in summary['best_configs']:
                logger.info(
                    f"  ✓ {config['model']} {config['quant']} - "
                    f"{config['profile']}: {config['status']}"
                )

        # Save results
        output_dir = args.output_dir or Path(config_mgr.get("output.directory", "results"))
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON results
        import json
        from dataclasses import asdict
        results_file = output_dir / "results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": summary,
                "test_runs": [asdict(run) for run in test_runs]
            }, f, indent=2)
        logger.info(f"\nResults saved to: {results_file}")

        logger.info("\n" + "=" * 60)
        logger.info("Matrix testing complete!")
        logger.info("=" * 60)

        # Return success if any tests passed
        return 0 if summary['passed'] > 0 else 1

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

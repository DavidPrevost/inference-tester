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

    # TODO: Implement main logic
    logger.info("Configuration: %s", args.config)
    logger.info("Models config: %s", args.models_config)

    if args.quick:
        logger.info("Mode: Quick test (~1 hour)")
    elif args.full:
        logger.info("Mode: Full test (~2-4 hours)")
    else:
        logger.info("Mode: Default")

    logger.warning("Implementation in progress - Phase 0 complete, Phase 1 next")

    return 0


if __name__ == "__main__":
    sys.exit(main())

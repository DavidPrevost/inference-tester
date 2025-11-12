"""CSV output formatter for test results.

Exports test results to CSV format for analysis in spreadsheet software.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class CSVFormatter:
    """Formats test results as CSV files."""

    @staticmethod
    def write_results(test_runs: List[Dict[str, Any]], output_path: Path):
        """Write test results to a CSV file.

        Args:
            test_runs: List of test run dictionaries
            output_path: Path to output CSV file
        """
        if not test_runs:
            logger.warning("No test runs to write to CSV")
            return

        logger.info(f"Writing results to CSV: {output_path}")

        # Determine all unique metric keys
        all_metric_keys = set()
        for run in test_runs:
            metrics = run.get("metrics", {})
            all_metric_keys.update(metrics.keys())

        all_metric_keys = sorted(all_metric_keys)

        # Build CSV headers
        headers = [
            "model_name",
            "quant",
            "profile_name",
            "status",
            "passed",
            "duration_seconds",
            "timestamp"
        ]
        headers.extend(all_metric_keys)
        headers.append("error")

        # Write CSV
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for run in test_runs:
                row = {
                    "model_name": run.get("model_name", ""),
                    "quant": run.get("quant", ""),
                    "profile_name": run.get("profile_name", ""),
                    "status": run.get("status", ""),
                    "passed": run.get("passed", False),
                    "duration_seconds": run.get("duration_seconds", 0),
                    "timestamp": run.get("timestamp", ""),
                    "error": run.get("error", "")
                }

                # Add metrics
                metrics = run.get("metrics", {})
                for key in all_metric_keys:
                    row[key] = metrics.get(key, "")

                writer.writerow(row)

        logger.info(f"CSV export complete: {len(test_runs)} rows written")

    @staticmethod
    def write_summary(summary: Dict[str, Any], output_path: Path):
        """Write summary statistics to a CSV file.

        Args:
            summary: Summary dictionary
            output_path: Path to output CSV file
        """
        logger.info(f"Writing summary to CSV: {output_path}")

        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])

            # Write simple metrics
            writer.writerow(["Total Tests", summary.get("total_tests", 0)])
            writer.writerow(["Passed", summary.get("passed", 0)])
            writer.writerow(["Failed", summary.get("failed", 0)])
            writer.writerow(["Skipped", summary.get("skipped", 0)])
            writer.writerow(["Excellent Configs", summary.get("excellent_configs", 0)])
            writer.writerow(["Good Configs", summary.get("good_configs", 0)])

            # Write status breakdown
            writer.writerow([])
            writer.writerow(["Status", "Count"])
            by_status = summary.get("by_status", {})
            for status, count in sorted(by_status.items()):
                writer.writerow([status, count])

        logger.info("Summary CSV export complete")

    @staticmethod
    def write_best_configs(best_configs: List[Dict[str, Any]], output_path: Path):
        """Write best configurations to a CSV file.

        Args:
            best_configs: List of best configuration dictionaries
            output_path: Path to output CSV file
        """
        if not best_configs:
            logger.warning("No best configs to write to CSV")
            return

        logger.info(f"Writing best configs to CSV: {output_path}")

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["model", "quant", "profile", "status"])
            writer.writeheader()

            for config in best_configs:
                writer.writerow(config)

        logger.info(f"Best configs CSV export complete: {len(best_configs)} configs")

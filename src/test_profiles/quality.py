"""Quality and accuracy test profile.

Tests model capability preservation across quantization levels
by running standardized test prompts.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from test_profiles.base import BaseProfile, TestResult
from utils.http import send_completion_request

logger = logging.getLogger(__name__)


class QualityProfile(BaseProfile):
    """Test profile for quality and accuracy evaluation.

    This profile tests model capability retention by measuring:
    - Accuracy on math problems (critical for financial work)
    - Reading comprehension scores
    - Logical reasoning ability
    - Format-following compliance

    Success criteria:
    - Math: ≥80% correct (financial accuracy critical)
    - Comprehension: ≥75% correct
    - Reasoning: ≥75% correct
    - Format: ≥90% compliance
    """

    name = "quality"
    description = "Quality/accuracy - capability preservation across quants"

    def run(self, server_url: str, config: Dict[str, Any]) -> TestResult:
        """Execute the quality test profile.

        Args:
            server_url: URL of the llama.cpp server
            config: Profile-specific configuration

        Returns:
            TestResult with metrics and status

        """
        logger.info(f"Running {self.name} profile")

        try:
            # Load test data
            test_data_path = config.get("test_data_path", "data/quality_tests.json")
            tests = self._load_test_data(test_data_path)

            if not tests:
                raise RuntimeError("No quality tests loaded")

            logger.info(f"Loaded {len(tests)} quality tests")

            # Run all tests
            results = []
            for test in tests:
                try:
                    result = self._run_test(server_url, test, config)
                    results.append(result)
                    logger.debug(
                        f"Test {test['id']} ({test['category']}): "
                        f"{'PASS' if result['correct'] else 'FAIL'}"
                    )
                except Exception as e:
                    logger.warning(f"Test {test['id']} failed to run: {e}")
                    results.append({
                        "id": test["id"],
                        "category": test["category"],
                        "correct": False,
                        "error": str(e)
                    })

            # Calculate metrics by category
            metrics = self._calculate_metrics(results)

            logger.info(
                "Quality test complete: Math=%.1f%%, Comprehension=%.1f%%, "
                "Reasoning=%.1f%%, Format=%.1f%%",
                metrics.get("math_accuracy", 0),
                metrics.get("comprehension_accuracy", 0),
                metrics.get("reasoning_accuracy", 0),
                metrics.get("format_accuracy", 0)
            )

            # Get thresholds
            thresholds = config.get("thresholds", {})

            # Classify result
            status = self.classify_result(metrics, thresholds)

            # Generate interpretations
            interpretation = self.interpret_metrics(metrics)

            return TestResult(
                profile=self.name,
                status=status,
                metrics=metrics,
                passed=(status in ["excellent", "good", "acceptable"]),
                interpretation=interpretation
            )

        except Exception as e:
            logger.error(f"Quality profile failed: {e}", exc_info=True)
            return TestResult(
                profile=self.name,
                status="error",
                metrics={},
                passed=False,
                error=str(e)
            )

    def _load_test_data(self, test_data_path: str) -> List[Dict[str, Any]]:
        """Load quality test data from JSON file.

        Args:
            test_data_path: Path to test data JSON file

        Returns:
            List of test definitions

        """
        path = Path(test_data_path)
        if not path.exists():
            logger.error(f"Test data file not found: {test_data_path}")
            return []

        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get("tests", [])
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            return []

    def _run_test(
        self,
        server_url: str,
        test: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single quality test.

        Args:
            server_url: Server URL
            test: Test definition
            config: Configuration

        Returns:
            Test result dictionary

        """
        # Send request to model
        response = send_completion_request(
            server_url,
            test["prompt"],
            max_tokens=200,
            temperature=0.1,  # Low temperature for consistency
            stream=False,
            timeout=60
        )

        # Extract response content
        content = response.get("content", "").strip()

        # Score the response
        correct = self._score_response(
            content,
            test["expected_answer"],
            test["scoring_type"],
            test.get("tolerance", 0)
        )

        return {
            "id": test["id"],
            "category": test["category"],
            "prompt": test["prompt"],
            "response": content,
            "expected": test["expected_answer"],
            "correct": correct
        }

    def _score_response(
        self,
        response: str,
        expected: str,
        scoring_type: str,
        tolerance: float = 0
    ) -> bool:
        """Score a model response.

        Args:
            response: Model's response
            expected: Expected answer
            scoring_type: Type of scoring to use
            tolerance: Tolerance for numeric comparisons

        Returns:
            True if response is correct

        """
        response_lower = response.lower().strip()
        expected_lower = expected.lower().strip()

        if scoring_type == "numeric":
            return self._score_numeric(response, expected, tolerance)
        elif scoring_type == "contains":
            return expected_lower in response_lower
        elif scoring_type == "json_valid":
            return self._score_json(response, expected)
        elif scoring_type == "format_check":
            return self._score_format(response, expected)
        else:
            # Default: exact match (case-insensitive)
            return response_lower == expected_lower

    def _score_numeric(self, response: str, expected: str, tolerance: float) -> bool:
        """Score a numeric response.

        Args:
            response: Model response
            expected: Expected numeric value
            tolerance: Acceptable tolerance

        Returns:
            True if numeric answer is within tolerance

        """
        try:
            # Extract first number from response
            numbers = re.findall(r'-?\d+\.?\d*', response)
            if not numbers:
                return False

            response_num = float(numbers[0])
            expected_num = float(expected)

            return abs(response_num - expected_num) <= tolerance

        except (ValueError, IndexError):
            return False

    def _score_json(self, response: str, expected: str) -> bool:
        """Score a JSON response.

        Args:
            response: Model response
            expected: Expected JSON structure (partial)

        Returns:
            True if response is valid JSON containing expected structure

        """
        try:
            # Try to parse as JSON
            parsed = json.loads(response)

            # Check if expected structure is present
            # For simplicity, check if expected string is in the JSON string
            response_str = json.dumps(parsed, separators=(',', ':'))
            expected_clean = expected.replace(" ", "")

            return expected_clean in response_str

        except (json.JSONDecodeError, TypeError):
            return False

    def _score_format(self, response: str, expected: str) -> bool:
        """Score a format-following response.

        Args:
            response: Model response
            expected: Expected format pattern

        Returns:
            True if response follows the expected format

        """
        # Check if response contains the expected comma-separated values
        # This is a simplified check - could be enhanced with regex
        response_clean = response.replace(" ", "").lower()
        expected_clean = expected.replace(" ", "").lower()

        # Count expected items
        expected_items = [item.strip() for item in expected.split(",")]
        found_count = sum(1 for item in expected_items if item.lower() in response_clean)

        # Require at least 80% of expected items
        return found_count >= len(expected_items) * 0.8

    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate metrics from test results.

        Args:
            results: List of test results

        Returns:
            Dictionary of metrics

        """
        # Group by category
        categories = {}
        for result in results:
            category = result["category"]
            if category not in categories:
                categories[category] = {"correct": 0, "total": 0}

            categories[category]["total"] += 1
            if result["correct"]:
                categories[category]["correct"] += 1

        # Calculate accuracy for each category
        metrics = {}
        for category, counts in categories.items():
            accuracy = (counts["correct"] / counts["total"] * 100) if counts["total"] > 0 else 0
            metrics[f"{category}_accuracy"] = accuracy
            metrics[f"{category}_correct"] = counts["correct"]
            metrics[f"{category}_total"] = counts["total"]

        # Calculate overall accuracy
        total_correct = sum(r["correct"] for r in results)
        total_tests = len(results)
        metrics["overall_accuracy"] = (total_correct / total_tests * 100) if total_tests > 0 else 0
        metrics["total_correct"] = total_correct
        metrics["total_tests"] = total_tests

        return metrics

    def interpret_metrics(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Convert metrics to human-readable interpretations.

        Args:
            metrics: Dictionary of metric values

        Returns:
            Dictionary of interpretations for each metric

        """
        interpretations = {}

        # Interpret overall accuracy
        overall = metrics.get("overall_accuracy", 0)
        if overall >= 90:
            interpretations["overall_accuracy"] = "Excellent, highly capable model"
        elif overall >= 80:
            interpretations["overall_accuracy"] = "Good, suitable for most tasks"
        elif overall >= 70:
            interpretations["overall_accuracy"] = "Acceptable, some limitations"
        elif overall >= 60:
            interpretations["overall_accuracy"] = "Poor, significant degradation"
        else:
            interpretations["overall_accuracy"] = "Failed, severe capability loss"

        # Interpret math accuracy
        math = metrics.get("math_accuracy", 0)
        if math >= 90:
            interpretations["math_accuracy"] = "Excellent, reliable for financial work"
        elif math >= 80:
            interpretations["math_accuracy"] = "Good, acceptable for basic calculations"
        elif math >= 70:
            interpretations["math_accuracy"] = "Marginal, verify all calculations"
        else:
            interpretations["math_accuracy"] = "Unreliable, do not use for financial tasks"

        # Interpret comprehension accuracy
        comp = metrics.get("comprehension_accuracy", 0)
        if comp >= 85:
            interpretations["comprehension_accuracy"] = "Excellent reading comprehension"
        elif comp >= 75:
            interpretations["comprehension_accuracy"] = "Good, handles most text well"
        elif comp >= 65:
            interpretations["comprehension_accuracy"] = "Acceptable, may miss nuances"
        else:
            interpretations["comprehension_accuracy"] = "Poor, struggles with text understanding"

        # Interpret reasoning accuracy
        reasoning = metrics.get("reasoning_accuracy", 0)
        if reasoning >= 85:
            interpretations["reasoning_accuracy"] = "Excellent logical reasoning"
        elif reasoning >= 75:
            interpretations["reasoning_accuracy"] = "Good, handles logic tasks well"
        elif reasoning >= 65:
            interpretations["reasoning_accuracy"] = "Acceptable, may make errors"
        else:
            interpretations["reasoning_accuracy"] = "Poor, unreliable for logic tasks"

        # Interpret format accuracy
        fmt = metrics.get("format_accuracy", 0)
        if fmt >= 95:
            interpretations["format_accuracy"] = "Excellent, very reliable for structured output"
        elif fmt >= 90:
            interpretations["format_accuracy"] = "Good, suitable for automation"
        elif fmt >= 80:
            interpretations["format_accuracy"] = "Acceptable, may need validation"
        else:
            interpretations["format_accuracy"] = "Poor, unreliable for structured tasks"

        return interpretations

    def get_required_context_size(self) -> int:
        """Return minimum context size for quality testing."""
        return 8192  # Need context for complex questions

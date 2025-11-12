"""Recommendation engine for test results.

Analyzes test results and provides actionable recommendations for model
selection and configuration.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates recommendations based on test results."""

    @staticmethod
    def generate_recommendations(
        test_runs: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on test results.

        Args:
            test_runs: List of test run dictionaries
            summary: Summary statistics dictionary

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Filter successful runs
        successful_runs = [
            run for run in test_runs
            if run.get("passed", False) and run.get("status") not in ["skipped", "error"]
        ]

        if not successful_runs:
            recommendations.append(
                "No configurations passed all tests. Consider testing smaller models "
                "or lower quantization levels (Q2_K, Q3_K_M) for your hardware."
            )
            return recommendations

        # Analyze by use case
        by_profile = {}
        for run in successful_runs:
            profile = run.get("profile_name", "unknown")
            if profile not in by_profile:
                by_profile[profile] = []
            by_profile[profile].append(run)

        # Generate use-case specific recommendations
        if "interactive" in by_profile:
            rec = RecommendationEngine._recommend_interactive(by_profile["interactive"])
            if rec:
                recommendations.append(rec)

        if "batch" in by_profile:
            rec = RecommendationEngine._recommend_batch(by_profile["batch"])
            if rec:
                recommendations.append(rec)

        if "long_context" in by_profile:
            rec = RecommendationEngine._recommend_long_context(by_profile["long_context"])
            if rec:
                recommendations.append(rec)

        if "quality" in by_profile:
            rec = RecommendationEngine._recommend_quality(by_profile["quality"])
            if rec:
                recommendations.append(rec)

        # General recommendations
        general_recs = RecommendationEngine._recommend_general(successful_runs, summary)
        recommendations.extend(general_recs)

        return recommendations

    @staticmethod
    def _recommend_interactive(runs: List[Dict[str, Any]]) -> str:
        """Recommend best config for interactive use.

        Args:
            runs: List of interactive profile runs

        Returns:
            Recommendation string or empty string
        """
        # Find runs with best responsiveness (low TTFT, high TPS)
        excellent = [r for r in runs if r.get("status") == "excellent"]

        if excellent:
            # Sort by tokens per second (descending)
            excellent.sort(
                key=lambda r: r.get("metrics", {}).get("tokens_per_sec", 0),
                reverse=True
            )
            best = excellent[0]

            return (
                f"Interactive/Creative Writing: Use {best['model_name']} ({best['quant']}) "
                f"for best experience - {best['metrics'].get('tokens_per_sec', 0):.1f} tokens/sec "
                f"with {best['metrics'].get('time_to_first_token', 0):.1f}s TTFT"
            )

        # Fall back to good runs
        good = [r for r in runs if r.get("status") == "good"]
        if good:
            good.sort(
                key=lambda r: r.get("metrics", {}).get("tokens_per_sec", 0),
                reverse=True
            )
            best = good[0]

            return (
                f"Interactive/Creative Writing: {best['model_name']} ({best['quant']}) "
                f"is acceptable - {best['metrics'].get('tokens_per_sec', 0):.1f} tokens/sec"
            )

        return ""

    @staticmethod
    def _recommend_batch(runs: List[Dict[str, Any]]) -> str:
        """Recommend best config for batch processing.

        Args:
            runs: List of batch profile runs

        Returns:
            Recommendation string or empty string
        """
        # Find runs with best throughput
        excellent = [r for r in runs if r.get("status") in ["excellent", "good"]]

        if excellent:
            # Sort by throughput (descending)
            excellent.sort(
                key=lambda r: r.get("metrics", {}).get("throughput_docs_per_hour", 0),
                reverse=True
            )
            best = excellent[0]

            return (
                f"Batch Processing: Use {best['model_name']} ({best['quant']}) "
                f"for highest throughput - {best['metrics'].get('throughput_docs_per_hour', 0):.1f} docs/hour"
            )

        return ""

    @staticmethod
    def _recommend_long_context(runs: List[Dict[str, Any]]) -> str:
        """Recommend best config for long context work.

        Args:
            runs: List of long_context profile runs

        Returns:
            Recommendation string or empty string
        """
        # Find runs with largest successful context
        successful = [
            r for r in runs
            if r.get("metrics", {}).get("max_successful_context", 0) > 0
        ]

        if successful:
            # Sort by max context size (descending)
            successful.sort(
                key=lambda r: r.get("metrics", {}).get("max_successful_context", 0),
                reverse=True
            )
            best = successful[0]
            max_ctx = best['metrics'].get('max_successful_context', 0)

            if max_ctx >= 32768:
                return (
                    f"Long Context Work: {best['model_name']} ({best['quant']}) "
                    f"handles up to {int(max_ctx)} tokens - excellent for lorebooks and plot tracking"
                )
            elif max_ctx >= 16384:
                return (
                    f"Long Context Work: {best['model_name']} ({best['quant']}) "
                    f"handles up to {int(max_ctx)} tokens - suitable for most long-form work"
                )
            else:
                return (
                    f"Long Context Work: Limited to {int(max_ctx)} tokens with "
                    f"{best['model_name']} ({best['quant']}) - consider breaking content into chunks"
                )

        return ""

    @staticmethod
    def _recommend_quality(runs: List[Dict[str, Any]]) -> str:
        """Recommend best config for quality-sensitive work.

        Args:
            runs: List of quality profile runs

        Returns:
            Recommendation string or empty string
        """
        # Find runs with best overall accuracy
        high_quality = [
            r for r in runs
            if r.get("metrics", {}).get("overall_accuracy", 0) >= 80
        ]

        if high_quality:
            # Sort by overall accuracy (descending)
            high_quality.sort(
                key=lambda r: r.get("metrics", {}).get("overall_accuracy", 0),
                reverse=True
            )
            best = high_quality[0]

            accuracy = best['metrics'].get('overall_accuracy', 0)
            math_acc = best['metrics'].get('math_accuracy', 0)

            if math_acc >= 90:
                return (
                    f"Financial/Accuracy Work: {best['model_name']} ({best['quant']}) "
                    f"maintains {accuracy:.1f}% overall accuracy with {math_acc:.1f}% math accuracy - "
                    "safe for financial tasks"
                )
            elif math_acc >= 80:
                return (
                    f"Accuracy Work: {best['model_name']} ({best['quant']}) "
                    f"maintains {accuracy:.1f}% overall accuracy - acceptable for most tasks, "
                    "but verify calculations for financial work"
                )

        return ""

    @staticmethod
    def _recommend_general(
        successful_runs: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> List[str]:
        """Generate general recommendations.

        Args:
            successful_runs: List of successful test runs
            summary: Summary statistics

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Count unique model/quant combinations that passed
        passed_configs = set()
        for run in successful_runs:
            passed_configs.add((run.get("model_name"), run.get("quant")))

        # Analyze quantization trends
        quant_success = {}
        for run in successful_runs:
            quant = run.get("quant")
            if quant not in quant_success:
                quant_success[quant] = 0
            quant_success[quant] += 1

        if quant_success:
            best_quant = max(quant_success, key=quant_success.get)
            if quant_success[best_quant] >= 3:
                recommendations.append(
                    f"Quantization Sweet Spot: {best_quant} provides the best balance "
                    f"of quality and performance for your hardware"
                )

        # Memory recommendations
        failed_runs = [r for r in successful_runs if r.get("status") == "failed"]
        if failed_runs:
            # Check for memory-related failures
            memory_failures = [
                r for r in failed_runs
                if "memory" in r.get("error", "").lower() or "swap" in r.get("error", "").lower()
            ]
            if memory_failures:
                recommendations.append(
                    "Memory Constraints: Consider closing background applications or "
                    "upgrading RAM for better results with larger models"
                )

        # Skipped tests recommendation
        skipped = summary.get("skipped", 0)
        total = summary.get("total_tests", 1)
        if skipped > total * 0.3:  # More than 30% skipped
            recommendations.append(
                f"Optimization: {skipped} tests were skipped due to hardware constraints. "
                "This is normal and saves testing time!"
            )

        # Success rate recommendation
        passed = summary.get("passed", 0)
        if passed > 0:
            pass_rate = (passed / (total - skipped)) * 100 if (total - skipped) > 0 else 0
            if pass_rate >= 80:
                recommendations.append(
                    f"Excellent Results: {pass_rate:.0f}% pass rate indicates your hardware "
                    "can handle most LLM workloads effectively"
                )
            elif pass_rate >= 50:
                recommendations.append(
                    f"Moderate Results: {pass_rate:.0f}% pass rate suggests selective model "
                    "choice is important for your hardware"
                )

        return recommendations

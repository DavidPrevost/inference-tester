"""Batch document processing test profile.

Tests throughput and stability for bulk document processing operations.
"""

import logging
import time
from typing import Any, Dict, List

from test_profiles.base import BaseProfile, TestResult
from utils.http import send_completion_request
from utils.hardware import get_memory_usage

logger = logging.getLogger(__name__)


# Sample documents for batch processing
SAMPLE_DOCUMENTS = [
    "Artificial intelligence is transforming industries worldwide, from healthcare to finance, enabling new capabilities and efficiencies that were previously impossible.",
    "Climate change continues to be one of the most pressing challenges of our time, requiring coordinated global action and innovative solutions to reduce emissions.",
    "The development of renewable energy technologies has accelerated rapidly, with solar and wind power becoming increasingly cost-competitive with traditional fossil fuels.",
    "Modern software development practices emphasize automation, continuous integration, and collaborative workflows to improve code quality and delivery speed.",
    "Quantum computing represents a paradigm shift in computational power, promising to solve complex problems that are currently intractable for classical computers.",
]

SUMMARY_PROMPT = "Please provide a concise one-sentence summary of the following text:\n\n{document}"


class BatchProfile(BaseProfile):
    """Test profile for batch document processing.

    This profile tests throughput and stability by measuring:
    - Average time per document
    - Standard deviation (consistency)
    - Throughput (documents/hour)
    - Memory usage over time
    - Performance degradation (first 10 vs last 10)

    Success criteria:
    - Variance < 20% (consistent performance)
    - No significant degradation over time
    - No memory leaks
    - Stable memory usage
    """

    name = "batch"
    description = "Batch document processing - throughput and stability"

    def run(self, server_url: str, config: Dict[str, Any]) -> TestResult:
        """Execute the batch processing test profile.

        Args:
            server_url: URL of the llama.cpp server
            config: Profile-specific configuration

        Returns:
            TestResult with metrics and status

        """
        logger.info(f"Running {self.name} profile")

        try:
            # Get configuration
            thresholds = config.get("thresholds", {})
            num_documents = thresholds.get("num_documents", 30)

            logger.info(f"Processing {num_documents} documents")

            # Process documents
            processing_times = []
            memory_samples = []

            for i in range(num_documents):
                # Select document (cycle through samples)
                doc = SAMPLE_DOCUMENTS[i % len(SAMPLE_DOCUMENTS)]
                prompt = SUMMARY_PROMPT.format(document=doc)

                # Measure processing time
                start_time = time.time()

                try:
                    response = send_completion_request(
                        server_url,
                        prompt,
                        max_tokens=100,
                        temperature=0.3,
                        stream=False,
                        timeout=60
                    )

                    end_time = time.time()
                    processing_time = end_time - start_time
                    processing_times.append(processing_time)

                    # Sample memory every 5 documents
                    if i % 5 == 0:
                        mem_used, _, _ = get_memory_usage()
                        memory_samples.append(mem_used)

                    logger.debug(f"Document {i+1}/{num_documents}: {processing_time:.2f}s")

                except Exception as e:
                    logger.warning(f"Document {i+1} failed: {e}")
                    # Continue with next document

            # Calculate metrics
            if not processing_times:
                raise RuntimeError("No documents processed successfully")

            avg_time = sum(processing_times) / len(processing_times)
            variance = self._calculate_variance(processing_times)

            # Calculate throughput (documents per hour)
            throughput = (len(processing_times) / sum(processing_times)) * 3600

            # Compare first 10 vs last 10
            degradation = self._calculate_degradation(processing_times)

            # Check for memory leaks
            memory_trend = self._analyze_memory_trend(memory_samples)

            metrics = {
                "avg_time_per_doc": avg_time,
                "variance_percent": variance,
                "throughput_docs_per_hour": throughput,
                "documents_processed": len(processing_times),
                "performance_degradation_percent": degradation,
                "memory_trend": memory_trend
            }

            logger.info(
                "Batch test complete: Throughput=%.1f docs/hr, Variance=%.1f%%",
                throughput, variance
            )

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
            logger.error(f"Batch profile failed: {e}", exc_info=True)
            return TestResult(
                profile=self.name,
                status="error",
                metrics={},
                passed=False,
                error=str(e)
            )

    def _calculate_variance(self, times: List[float]) -> float:
        """Calculate variance of processing times.

        Args:
            times: List of processing times

        Returns:
            Variance as percentage
        """
        if len(times) < 2:
            return 0.0

        mean = sum(times) / len(times)
        if mean == 0:
            return 0.0

        variance_sum = sum((t - mean) ** 2 for t in times)
        std_dev = (variance_sum / len(times)) ** 0.5

        return (std_dev / mean) * 100

    def _calculate_degradation(self, times: List[float]) -> float:
        """Calculate performance degradation over time.

        Args:
            times: List of processing times in order

        Returns:
            Degradation percentage (positive means slower over time)
        """
        if len(times) < 20:
            return 0.0

        # Compare first 10 vs last 10
        first_10 = times[:10]
        last_10 = times[-10:]

        avg_first = sum(first_10) / len(first_10)
        avg_last = sum(last_10) / len(last_10)

        if avg_first == 0:
            return 0.0

        return ((avg_last - avg_first) / avg_first) * 100

    def _analyze_memory_trend(self, samples: List[float]) -> float:
        """Analyze memory usage trend.

        Args:
            samples: Memory usage samples over time

        Returns:
            Memory growth in GB
        """
        if len(samples) < 2:
            return 0.0

        return samples[-1] - samples[0]

    def interpret_metrics(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Convert metrics to human-readable interpretations.

        Args:
            metrics: Dictionary of metric values

        Returns:
            Dictionary of interpretations for each metric
        """
        interpretations = {}

        # Interpret throughput
        throughput = metrics.get("throughput_docs_per_hour", 0)
        if throughput >= 120:
            interpretations["throughput_docs_per_hour"] = "Excellent throughput"
        elif throughput >= 60:
            interpretations["throughput_docs_per_hour"] = "Good, efficient bulk processing"
        elif throughput >= 30:
            interpretations["throughput_docs_per_hour"] = "Acceptable for moderate batches"
        elif throughput >= 10:
            interpretations["throughput_docs_per_hour"] = "Slow, overnight batch jobs only"
        else:
            interpretations["throughput_docs_per_hour"] = "Very slow, impractical for batches"

        # Interpret variance
        variance = metrics.get("variance_percent", 0)
        if variance < 10:
            interpretations["variance_percent"] = "Very consistent performance"
        elif variance < 20:
            interpretations["variance_percent"] = "Reasonably consistent"
        elif variance < 30:
            interpretations["variance_percent"] = "Somewhat inconsistent"
        else:
            interpretations["variance_percent"] = "Highly variable, unpredictable"

        # Interpret degradation
        degradation = metrics.get("performance_degradation_percent", 0)
        if abs(degradation) < 5:
            interpretations["performance_degradation_percent"] = "Stable, no degradation"
        elif degradation < 15:
            interpretations["performance_degradation_percent"] = "Slight slowdown over time"
        elif degradation < 30:
            interpretations["performance_degradation_percent"] = "Noticeable degradation"
        else:
            interpretations["performance_degradation_percent"] = "Significant performance loss"

        return interpretations

    def get_required_context_size(self) -> int:
        """Return minimum context size for batch testing."""
        return 4096  # Moderate context for document summaries

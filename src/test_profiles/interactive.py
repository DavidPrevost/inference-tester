"""Interactive storytelling test profile.

Tests responsiveness for creative writing workflows by measuring
Time to First Token (TTFT) and streaming speed.
"""

import logging
import time
from typing import Any, Dict, List

from test_profiles.base import BaseProfile, TestResult
from utils.http import stream_completion

logger = logging.getLogger(__name__)


# Test prompt for story generation
TEST_PROMPT = """You are a creative writer. Continue this story with vivid details and engaging narrative:

The old lighthouse stood silent against the stormy sky. Sarah had inherited it from her grandmother just last week, and tonight was her first night staying there alone. As she climbed the spiral staircase with her lantern, she noticed something strange—"""


class InteractiveProfile(BaseProfile):
    """Test profile for interactive storytelling use case.

    This profile tests responsiveness for creative writing by measuring:
    - Time to First Token (TTFT)
    - Tokens per second during streaming
    - Consistency of token timing

    Success criteria:
    - TTFT ≤ 30 seconds
    - Streaming ≥ 2 tokens/sec
    - Consistent timing (low variance)
    """

    name = "interactive"
    description = "Interactive storytelling - TTFT and streaming speed"

    def run(self, server_url: str, config: Dict[str, Any]) -> TestResult:
        """Execute the interactive test profile.

        Args:
            server_url: URL of the llama.cpp server
            config: Profile-specific configuration

        Returns:
            TestResult with metrics and status

        """
        logger.info(f"Running {self.name} profile")

        try:
            # Stream tokens and collect timing data
            ttft, tokens_per_sec, token_times = self._measure_streaming_performance(
                server_url,
                max_tokens=500
            )

            # Calculate variance in token timing
            variance = self._calculate_variance(token_times)

            # Collect metrics
            metrics = {
                "time_to_first_token": ttft,
                "tokens_per_sec": tokens_per_sec,
                "variance_percent": variance,
                "total_tokens": len(token_times)
            }

            logger.info(
                "Interactive test complete: TTFT=%.2fs, Speed=%.1f t/s, Variance=%.1f%%",
                ttft, tokens_per_sec, variance
            )

            # Get thresholds from config
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
            logger.error(f"Interactive profile failed: {e}", exc_info=True)
            return TestResult(
                profile=self.name,
                status="error",
                metrics={},
                passed=False,
                error=str(e)
            )

    def _measure_streaming_performance(
        self,
        server_url: str,
        max_tokens: int = 500
    ) -> tuple:
        """Measure TTFT and streaming performance.

        Args:
            server_url: Server URL
            max_tokens: Maximum tokens to generate

        Returns:
            Tuple of (ttft, tokens_per_sec, token_times)

        """
        logger.debug("Starting streaming performance measurement")

        start_time = time.time()
        first_token_time = None
        token_times: List[float] = []

        try:
            for chunk in stream_completion(
                server_url,
                TEST_PROMPT,
                max_tokens=max_tokens,
                temperature=0.7
            ):
                current_time = time.time()

                # Record TTFT
                if first_token_time is None:
                    first_token_time = current_time
                    ttft = first_token_time - start_time
                    logger.debug(f"First token received after {ttft:.2f}s")

                # Record token timing
                if "content" in chunk or "token" in chunk:
                    token_times.append(current_time)

                # Stop condition
                if chunk.get("stop", False):
                    break

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            raise

        # Calculate metrics
        if first_token_time is None:
            raise RuntimeError("No tokens received from server")

        end_time = time.time()
        total_time = end_time - first_token_time  # Time from first token to last
        total_tokens = len(token_times)

        if total_time > 0 and total_tokens > 0:
            tokens_per_sec = total_tokens / total_time
        else:
            tokens_per_sec = 0.0

        logger.debug(
            f"Streaming complete: {total_tokens} tokens in {total_time:.2f}s "
            f"({tokens_per_sec:.1f} t/s)"
        )

        return ttft, tokens_per_sec, token_times

    def _calculate_variance(self, token_times: List[float]) -> float:
        """Calculate variance in token timing.

        Args:
            token_times: List of token arrival timestamps

        Returns:
            Variance as a percentage

        """
        if len(token_times) < 2:
            return 0.0

        # Calculate intervals between tokens
        intervals = []
        for i in range(1, len(token_times)):
            interval = token_times[i] - token_times[i-1]
            intervals.append(interval)

        if not intervals:
            return 0.0

        # Calculate mean and standard deviation
        mean = sum(intervals) / len(intervals)
        if mean == 0:
            return 0.0

        variance_sum = sum((x - mean) ** 2 for x in intervals)
        std_dev = (variance_sum / len(intervals)) ** 0.5

        # Return as percentage of mean
        variance_percent = (std_dev / mean) * 100
        return variance_percent

    def interpret_metrics(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Convert metrics to human-readable interpretations.

        Args:
            metrics: Dictionary of metric values

        Returns:
            Dictionary of interpretations for each metric

        """
        interpretations = {}

        # Interpret tokens per second
        tps = metrics.get("tokens_per_sec", 0)
        if tps < 2:
            interpretations["tokens_per_sec"] = "Very slow, barely usable"
        elif tps < 5:
            interpretations["tokens_per_sec"] = "Slow but readable, like careful dictation"
        elif tps < 10:
            interpretations["tokens_per_sec"] = "Moderate pace, acceptable"
        elif tps < 15:
            interpretations["tokens_per_sec"] = "Comfortable reading speed"
        elif tps < 20:
            interpretations["tokens_per_sec"] = "Fast reading, feels responsive"
        elif tps < 30:
            interpretations["tokens_per_sec"] = "Very fast, excellent UX"
        else:
            interpretations["tokens_per_sec"] = "Nearly instant for most prompts"

        # Interpret TTFT
        ttft = metrics.get("time_to_first_token", 0)
        if ttft < 2:
            interpretations["time_to_first_token"] = "Feels instant, excellent UX"
        elif ttft < 5:
            interpretations["time_to_first_token"] = "Barely noticeable pause"
        elif ttft < 10:
            interpretations["time_to_first_token"] = "Noticeable but acceptable"
        elif ttft < 30:
            interpretations["time_to_first_token"] = "Significant wait, breaks flow"
        else:
            interpretations["time_to_first_token"] = "Frustrating, unusable for interactive work"

        # Interpret variance
        variance = metrics.get("variance_percent", 0)
        if variance < 10:
            interpretations["variance_percent"] = "Very consistent, smooth output"
        elif variance < 20:
            interpretations["variance_percent"] = "Reasonably consistent"
        elif variance < 30:
            interpretations["variance_percent"] = "Somewhat inconsistent"
        else:
            interpretations["variance_percent"] = "Highly variable, choppy output"

        return interpretations

    def get_required_context_size(self) -> int:
        """Return minimum context size for interactive testing."""
        return 4096  # Need reasonable context for story prompts

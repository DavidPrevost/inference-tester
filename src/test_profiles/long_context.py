"""Long context management test profile.

Tests ability to handle large context windows for use cases like
lorebooks, character rosters, and plot tracking.
"""

import logging
import time
from typing import Any, Dict, List

from test_profiles.base import BaseProfile, TestResult
from utils.http import send_completion_request
from utils.hardware import get_memory_usage, get_swap_usage

logger = logging.getLogger(__name__)


def generate_test_context(num_tokens: int) -> str:
    """Generate a test context of approximately the given token count.

    Args:
        num_tokens: Target number of tokens

    Returns:
        Test context string
    """
    # Approximate: 1 token ~= 4 characters for English text
    # Generate repetitive but valid text content
    words_per_token = 0.75  # Conservative estimate
    num_words = int(num_tokens * words_per_token)

    # Create a story-like context with repeated elements
    base_text = (
        "The ancient library contained countless volumes of knowledge. "
        "Each shelf held mysteries waiting to be discovered. "
        "Scholars from distant lands came to study the rare manuscripts. "
        "The keeper of the library knew every book by heart. "
    )

    # Repeat to reach desired length
    repetitions = (num_words // 20) + 1
    context = base_text * repetitions

    # Add a clear instruction at the end
    context += "\n\nBased on the above context, please provide a brief summary."

    return context


class LongContextProfile(BaseProfile):
    """Test profile for long context management.

    This profile tests ability to handle large context windows by measuring:
    - Initial context load time
    - Maximum usable context size
    - Memory usage
    - Processing speed at various context sizes

    Success criteria:
    - Initial load ≤ 60 seconds
    - No swapping to disk
    - Successful generation at target context size
    """

    name = "long_context"
    description = "Long context management - large context handling"

    def run(self, server_url: str, config: Dict[str, Any]) -> TestResult:
        """Execute the long context test profile.

        Args:
            server_url: URL of the llama.cpp server
            config: Profile-specific configuration

        Returns:
            TestResult with metrics and status

        """
        logger.info(f"Running {self.name} profile")

        try:
            # Get test sizes from config
            thresholds = config.get("thresholds", {})
            test_sizes = thresholds.get("test_sizes", [4096, 8192, 16384, 32768])

            logger.info(f"Testing context sizes: {test_sizes}")

            # Test each context size
            results = []
            max_successful_size = 0
            total_max_load_time = 0

            for size in test_sizes:
                logger.info(f"Testing context size: {size} tokens")

                result = self._test_context_size(server_url, size, thresholds)
                results.append(result)

                if result["success"]:
                    max_successful_size = size
                    total_max_load_time = max(total_max_load_time, result["load_time"])
                else:
                    # Stop testing larger sizes if this one failed
                    logger.info(f"Context size {size} failed, stopping progression")
                    break

            # Calculate aggregate metrics
            if results:
                avg_load_time = sum(r["load_time"] for r in results if r["success"]) / max(1, sum(1 for r in results if r["success"]))
            else:
                avg_load_time = 0

            metrics = {
                "max_successful_context": max_successful_size,
                "max_load_time": total_max_load_time,
                "avg_load_time": avg_load_time,
                "contexts_tested": len(results),
                "contexts_successful": sum(1 for r in results if r["success"])
            }

            logger.info(
                "Long context test complete: Max=%d tokens, Load=%.2fs",
                max_successful_size, total_max_load_time
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
            logger.error(f"Long context profile failed: {e}", exc_info=True)
            return TestResult(
                profile=self.name,
                status="error",
                metrics={},
                passed=False,
                error=str(e)
            )

    def _test_context_size(
        self,
        server_url: str,
        context_size: int,
        thresholds: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test a specific context size.

        Args:
            server_url: Server URL
            context_size: Context size in tokens
            thresholds: Configuration thresholds

        Returns:
            Dictionary with test results
        """
        # Generate test context
        context = generate_test_context(context_size)

        # Check memory before test
        mem_before, _, _ = get_memory_usage()
        swap_before, _ = get_swap_usage()

        # Measure load time and generation
        start_time = time.time()

        try:
            response = send_completion_request(
                server_url,
                context,
                max_tokens=50,  # Short response to test context only
                temperature=0.3,
                stream=False,
                timeout=120  # 2 minute timeout for large contexts
            )

            end_time = time.time()
            load_time = end_time - start_time

            # Check memory after test
            mem_after, _, _ = get_memory_usage()
            swap_after, _ = get_swap_usage()

            # Check for swapping
            swap_used = swap_after > swap_before

            success = not swap_used and "content" in response
            logger.debug(
                f"Context {context_size}: load_time={load_time:.2f}s, "
                f"mem_delta={mem_after - mem_before:.2f}GB, swap={swap_used}"
            )

            return {
                "size": context_size,
                "load_time": load_time,
                "memory_used": mem_after - mem_before,
                "swap_used": swap_used,
                "success": success
            }

        except Exception as e:
            logger.warning(f"Context size {context_size} failed: {e}")
            return {
                "size": context_size,
                "load_time": 0,
                "memory_used": 0,
                "swap_used": False,
                "success": False
            }

    def interpret_metrics(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Convert metrics to human-readable interpretations.

        Args:
            metrics: Dictionary of metric values

        Returns:
            Dictionary of interpretations for each metric
        """
        interpretations = {}

        # Interpret max successful context
        max_ctx = metrics.get("max_successful_context", 0)
        if max_ctx >= 32768:
            interpretations["max_successful_context"] = "Excellent, handles very large contexts"
        elif max_ctx >= 16384:
            interpretations["max_successful_context"] = "Good, suitable for most long-form work"
        elif max_ctx >= 8192:
            interpretations["max_successful_context"] = "Acceptable for moderate context needs"
        elif max_ctx >= 4096:
            interpretations["max_successful_context"] = "Limited, only basic context support"
        else:
            interpretations["max_successful_context"] = "Poor, cannot handle standard contexts"

        # Interpret load time
        load_time = metrics.get("max_load_time", 0)
        if load_time < 5:
            interpretations["max_load_time"] = "Very fast, smooth workflow"
        elif load_time < 15:
            interpretations["max_load_time"] = "Fast, brief pause"
        elif load_time < 30:
            interpretations["max_load_time"] = "Moderate, noticeable delay"
        elif load_time < 60:
            interpretations["max_load_time"] = "Slow, coffee break territory"
        else:
            interpretations["max_load_time"] = "Very slow, impractical for interactive work"

        return interpretations

    def get_required_context_size(self) -> int:
        """Return minimum context size for long context testing."""
        return 65536  # Test up to 64k context

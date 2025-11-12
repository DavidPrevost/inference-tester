"""Interactive storytelling test profile.

Tests responsiveness for creative writing workflows by measuring
Time to First Token (TTFT) and streaming speed.
"""

import logging
from typing import Any, Dict

from test_profiles.base import BaseProfile, TestResult

logger = logging.getLogger(__name__)


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

        # TODO: Implement interactive testing
        # 1. Send prompt requesting 500-token story continuation
        # 2. Measure time until first token arrives
        # 3. Measure average tokens/sec during generation
        # 4. Measure variance in token timing

        return TestResult(
            profile=self.name,
            status="error",
            metrics={},
            passed=False,
            error="Not yet implemented"
        )

    def get_required_context_size(self) -> int:
        """Return minimum context size for interactive testing."""
        return 4096  # Need reasonable context for story prompts

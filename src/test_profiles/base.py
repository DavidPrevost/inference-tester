"""Base class for all test profiles.

This module defines the abstract base class that all test profiles must
inherit from, providing a consistent interface and shared functionality.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result from a test profile execution.

    Attributes:
        profile: Profile name
        status: Status classification (excellent, good, acceptable, poor, failed, error)
        metrics: Dictionary of metric values
        passed: Whether the test passed minimum thresholds
        error: Error message if status is "error"
        interpretation: Human-readable metric interpretations
        details: Additional details about the test

    """
    profile: str
    status: str
    metrics: Dict[str, float]
    passed: bool
    error: Optional[str] = None
    interpretation: Optional[Dict[str, str]] = None
    details: Optional[Dict[str, Any]] = field(default_factory=dict)


class BaseProfile(ABC):
    """Abstract base class for all test profiles.

    All test profiles must inherit from this class and implement the
    run() method. This ensures a consistent interface across all profiles.
    """

    # Profile metadata - subclasses should override these
    name: str = "base"
    description: str = "Base profile"

    def __init__(self):
        """Initialize the profile."""
        self.logger = logging.getLogger(f"{__name__}.{self.name}")

    @abstractmethod
    def run(self, server_url: str, config: Dict[str, Any]) -> TestResult:
        """Execute the test profile.

        This is the main method that performs the actual testing. Each profile
        implements its own testing logic here.

        Args:
            server_url: URL of the llama.cpp server
            config: Profile-specific configuration from config.yaml

        Returns:
            TestResult with metrics and status

        Raises:
            Exception: If test execution fails critically

        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate profile-specific configuration.

        Args:
            config: Configuration dictionary for this profile

        Returns:
            True if configuration is valid, False otherwise

        """
        # Default implementation accepts any config
        return True

    def get_required_context_size(self) -> int:
        """Return minimum context size needed for this profile.

        Returns:
            Minimum context size in tokens

        """
        return 2048  # Default context size

    def interpret_metrics(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Convert metrics to human-readable interpretations.

        Args:
            metrics: Dictionary of metric values

        Returns:
            Dictionary of interpretations for each metric

        """
        # Default implementation returns empty dict
        # Subclasses should override to provide interpretations
        return {}

    def classify_result(
        self,
        metrics: Dict[str, float],
        thresholds: Dict[str, float]
    ) -> str:
        """Classify test result based on metrics and thresholds.

        Args:
            metrics: Measured metric values
            thresholds: Threshold values for classification

        Returns:
            Classification: "excellent", "good", "acceptable", "poor", or "failed"

        """
        # Default implementation - subclasses can override for custom logic
        # This is a simple threshold-based classification

        if not thresholds:
            return "unknown"

        # Check if all metrics meet minimum thresholds
        all_met = True
        exceed_by_50_percent = True
        exceed_by_20_percent = True

        for key, threshold in thresholds.items():
            if key.startswith("min_"):
                metric_key = key[4:]  # Remove "min_" prefix
                metric_value = metrics.get(metric_key, 0)

                if metric_value < threshold:
                    all_met = False
                    exceed_by_50_percent = False
                    exceed_by_20_percent = False
                elif metric_value < threshold * 1.2:
                    exceed_by_50_percent = False
                    exceed_by_20_percent = False
                elif metric_value < threshold * 1.5:
                    exceed_by_50_percent = False

            elif key.startswith("max_"):
                metric_key = key[4:]  # Remove "max_" prefix
                metric_value = metrics.get(metric_key, float('inf'))

                if metric_value > threshold:
                    all_met = False
                    exceed_by_50_percent = False
                    exceed_by_20_percent = False
                elif metric_value > threshold * 0.8:
                    exceed_by_50_percent = False
                    exceed_by_20_percent = False
                elif metric_value > threshold * 0.67:
                    exceed_by_50_percent = False

        if not all_met:
            return "failed"
        elif exceed_by_50_percent:
            return "excellent"
        elif exceed_by_20_percent:
            return "good"
        else:
            return "acceptable"

"""System stress test profile.

Tests sustained operation and thermal behavior under continuous load.
"""

import logging
import time
from typing import Any, Dict, List

from test_profiles.base import BaseProfile, TestResult
from utils.http import stream_completion
from utils.hardware import (
    get_cpu_temperature,
    get_cpu_frequency,
    get_memory_usage,
    get_swap_usage
)

logger = logging.getLogger(__name__)


# Test prompt for continuous generation
STRESS_PROMPT = """Write a detailed story about a character's journey. Include vivid descriptions, dialogue, and character development. Make it engaging and creative."""


class StressProfile(BaseProfile):
    """Test profile for system stress and stability.

    This profile tests sustained operation by measuring:
    - CPU temperature over time
    - Thermal throttling events
    - Swap usage
    - System responsiveness
    - Sustained tokens/sec consistency

    Success criteria:
    - Temperature ≤ 85°C
    - No thermal throttling
    - No swap usage
    - Stable performance throughout
    - System remains responsive

    Note: This profile runs LAST and selects model based on prior
    benchmark results (uses last or next-to-last passing config).
    """

    name = "stress"
    description = "System stress - sustained load and thermal behavior"

    def run(self, server_url: str, config: Dict[str, Any]) -> TestResult:
        """Execute the stress test profile.

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
            duration_minutes = thresholds.get("duration_minutes", 30)
            sample_interval = thresholds.get("sample_interval", 30)  # seconds
            max_safe_temp = thresholds.get("max_safe_temp", 90)  # °C

            logger.info(
                f"Starting stress test: {duration_minutes} minutes, "
                f"sampling every {sample_interval}s"
            )

            # Run continuous load test
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)

            # Tracking data
            temperature_samples = []
            frequency_samples = []
            memory_samples = []
            swap_samples = []
            generation_times = []
            token_counts = []

            iteration = 0
            aborted = False
            abort_reason = None

            while time.time() < end_time:
                iteration += 1
                iter_start = time.time()

                logger.debug(f"Stress iteration {iteration}")

                # Collect system vitals before generation
                temp = get_cpu_temperature()
                freq = get_cpu_frequency()
                mem_used, _, _ = get_memory_usage()
                swap_used, _ = get_swap_usage()

                # Check for dangerous temperature
                if temp and temp > max_safe_temp:
                    logger.error(f"Temperature critical: {temp}°C - aborting stress test")
                    aborted = True
                    abort_reason = f"Critical temperature: {temp}°C"
                    break

                # Record vitals
                if temp is not None:
                    temperature_samples.append(temp)
                if freq is not None:
                    frequency_samples.append(freq)
                memory_samples.append(mem_used)
                swap_samples.append(swap_used)

                # Run a generation
                try:
                    token_count, gen_time = self._run_generation(server_url)
                    generation_times.append(gen_time)
                    token_counts.append(token_count)
                except Exception as e:
                    logger.warning(f"Generation failed in iteration {iteration}: {e}")
                    # Continue to next iteration

                # Sleep until next sample interval
                iter_elapsed = time.time() - iter_start
                sleep_time = max(0, sample_interval - iter_elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            # Calculate metrics
            elapsed_time = time.time() - start_time
            elapsed_minutes = elapsed_time / 60

            metrics = {
                "duration_minutes": elapsed_minutes,
                "iterations": iteration,
                "aborted": aborted
            }

            # Temperature metrics
            if temperature_samples:
                metrics["avg_temperature"] = sum(temperature_samples) / len(temperature_samples)
                metrics["max_temperature"] = max(temperature_samples)
                metrics["min_temperature"] = min(temperature_samples)
                metrics["temp_variance"] = self._calculate_variance_simple(temperature_samples)

            # Frequency metrics (throttling detection)
            if frequency_samples and len(frequency_samples) > 1:
                base_freq = frequency_samples[0]
                metrics["avg_frequency"] = sum(frequency_samples) / len(frequency_samples)
                metrics["min_frequency"] = min(frequency_samples)

                # Detect throttling (frequency drops)
                if base_freq > 0:
                    freq_drop = ((base_freq - min(frequency_samples)) / base_freq) * 100
                    metrics["frequency_drop_percent"] = freq_drop
                    metrics["throttling_detected"] = freq_drop > 10  # >10% drop = throttling

            # Memory metrics
            if memory_samples:
                metrics["avg_memory_gb"] = sum(memory_samples) / len(memory_samples)
                metrics["max_memory_gb"] = max(memory_samples)
                metrics["memory_growth_gb"] = memory_samples[-1] - memory_samples[0]

            # Swap metrics
            if swap_samples:
                metrics["max_swap_gb"] = max(swap_samples)
                metrics["swap_used"] = any(s > 0.1 for s in swap_samples)  # >100MB

            # Performance metrics
            if generation_times:
                metrics["avg_generation_time"] = sum(generation_times) / len(generation_times)

            if token_counts and generation_times:
                total_tokens = sum(token_counts)
                total_time = sum(generation_times)
                metrics["avg_tokens_per_sec"] = total_tokens / total_time if total_time > 0 else 0

                # Performance degradation (first 5 vs last 5)
                degradation = self._calculate_performance_degradation(
                    token_counts,
                    generation_times
                )
                metrics["performance_degradation_percent"] = degradation

            if aborted:
                metrics["abort_reason"] = abort_reason

            logger.info(
                "Stress test complete: %.1f minutes, Temp=%.1f°C, T/s=%.1f",
                elapsed_minutes,
                metrics.get("avg_temperature", 0),
                metrics.get("avg_tokens_per_sec", 0)
            )

            # Classify result
            status = self.classify_result(metrics, thresholds)

            # Generate interpretations
            interpretation = self.interpret_metrics(metrics)

            # Pass if not aborted and status is acceptable
            passed = not aborted and status in ["excellent", "good", "acceptable"]

            return TestResult(
                profile=self.name,
                status=status if not aborted else "failed",
                metrics=metrics,
                passed=passed,
                interpretation=interpretation,
                error=abort_reason if aborted else None
            )

        except Exception as e:
            logger.error(f"Stress profile failed: {e}", exc_info=True)
            return TestResult(
                profile=self.name,
                status="error",
                metrics={},
                passed=False,
                error=str(e)
            )

    def _run_generation(self, server_url: str) -> tuple:
        """Run a single generation and measure performance.

        Args:
            server_url: Server URL

        Returns:
            Tuple of (token_count, generation_time)

        """
        start_time = time.time()
        token_count = 0

        try:
            for chunk in stream_completion(
                server_url,
                STRESS_PROMPT,
                max_tokens=300,
                temperature=0.7
            ):
                # Count tokens
                if "content" in chunk or "token" in chunk:
                    token_count += 1

                # Stop condition
                if chunk.get("stop", False):
                    break

        except Exception as e:
            logger.warning(f"Generation stream error: {e}")
            raise

        generation_time = time.time() - start_time
        return token_count, generation_time

    def _calculate_variance_simple(self, values: List[float]) -> float:
        """Calculate variance of a list of values.

        Args:
            values: List of numeric values

        Returns:
            Variance (standard deviation)

        """
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance_sum = sum((x - mean) ** 2 for x in values)
        std_dev = (variance_sum / len(values)) ** 0.5

        return std_dev

    def _calculate_performance_degradation(
        self,
        token_counts: List[int],
        generation_times: List[float]
    ) -> float:
        """Calculate performance degradation over time.

        Args:
            token_counts: List of token counts per generation
            generation_times: List of generation times

        Returns:
            Degradation percentage (positive = slower over time)

        """
        if len(token_counts) < 10:
            return 0.0

        # Calculate tokens/sec for each generation
        tps_values = []
        for tokens, time_val in zip(token_counts, generation_times):
            if time_val > 0:
                tps_values.append(tokens / time_val)

        if len(tps_values) < 10:
            return 0.0

        # Compare first 5 vs last 5
        first_5 = tps_values[:5]
        last_5 = tps_values[-5:]

        avg_first = sum(first_5) / len(first_5)
        avg_last = sum(last_5) / len(last_5)

        if avg_first == 0:
            return 0.0

        # Negative degradation = performance improved (unusual but possible)
        return ((avg_first - avg_last) / avg_first) * 100

    def interpret_metrics(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Convert metrics to human-readable interpretations.

        Args:
            metrics: Dictionary of metric values

        Returns:
            Dictionary of interpretations for each metric

        """
        interpretations = {}

        # Interpret temperature
        max_temp = metrics.get("max_temperature", 0)
        if max_temp:
            if max_temp < 65:
                interpretations["max_temperature"] = "Excellent, very cool operation"
            elif max_temp < 75:
                interpretations["max_temperature"] = "Good, comfortable temperatures"
            elif max_temp < 85:
                interpretations["max_temperature"] = "Warm but acceptable"
            elif max_temp < 90:
                interpretations["max_temperature"] = "Hot, approaching limits"
            else:
                interpretations["max_temperature"] = "Critical, thermal throttling likely"

        # Interpret throttling
        throttling = metrics.get("throttling_detected", False)
        freq_drop = metrics.get("frequency_drop_percent", 0)
        if throttling:
            interpretations["throttling_detected"] = f"Yes, {freq_drop:.1f}% frequency drop"
        else:
            interpretations["throttling_detected"] = "No throttling detected"

        # Interpret memory growth
        mem_growth = metrics.get("memory_growth_gb", 0)
        if abs(mem_growth) < 0.5:
            interpretations["memory_growth_gb"] = "Stable, no memory leak"
        elif mem_growth < 1.0:
            interpretations["memory_growth_gb"] = "Slight growth, likely normal"
        elif mem_growth < 2.0:
            interpretations["memory_growth_gb"] = "Moderate growth, monitor"
        else:
            interpretations["memory_growth_gb"] = "Significant growth, possible leak"

        # Interpret swap usage
        swap_used = metrics.get("swap_used", False)
        if swap_used:
            interpretations["swap_used"] = "Yes, insufficient RAM"
        else:
            interpretations["swap_used"] = "No swapping, sufficient RAM"

        # Interpret performance degradation
        degradation = metrics.get("performance_degradation_percent", 0)
        if degradation < 5:
            interpretations["performance_degradation_percent"] = "Stable, no degradation"
        elif degradation < 10:
            interpretations["performance_degradation_percent"] = "Slight slowdown"
        elif degradation < 20:
            interpretations["performance_degradation_percent"] = "Noticeable degradation"
        else:
            interpretations["performance_degradation_percent"] = "Significant performance loss"

        # Interpret tokens per second
        tps = metrics.get("avg_tokens_per_sec", 0)
        if tps >= 10:
            interpretations["avg_tokens_per_sec"] = "Excellent sustained throughput"
        elif tps >= 5:
            interpretations["avg_tokens_per_sec"] = "Good, comfortable speed"
        elif tps >= 2:
            interpretations["avg_tokens_per_sec"] = "Acceptable for long-running tasks"
        else:
            interpretations["avg_tokens_per_sec"] = "Slow, impractical for extended use"

        return interpretations

    def get_required_context_size(self) -> int:
        """Return minimum context size for stress testing."""
        return 8192  # Moderate context for sustained testing

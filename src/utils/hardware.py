"""Hardware detection and monitoring utilities.

This module provides functions for detecting and monitoring hardware
resources including memory, CPU, and temperature.
"""

import logging
import os
import platform
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def get_available_memory() -> float:
    """Get available system memory in GB.

    Returns:
        Available memory in GB

    """
    try:
        import psutil
        mem = psutil.virtual_memory()
        return mem.available / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not available, cannot detect memory")
        return 0.0


def get_total_memory() -> float:
    """Get total system memory in GB.

    Returns:
        Total memory in GB

    """
    try:
        import psutil
        mem = psutil.virtual_memory()
        return mem.total / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not available, cannot detect memory")
        return 0.0


def get_memory_usage() -> Tuple[float, float, float]:
    """Get current memory usage statistics.

    Returns:
        Tuple of (used_gb, available_gb, percent_used)

    """
    try:
        import psutil
        mem = psutil.virtual_memory()
        return (
            mem.used / (1024 ** 3),
            mem.available / (1024 ** 3),
            mem.percent
        )
    except ImportError:
        return (0.0, 0.0, 0.0)


def get_swap_usage() -> Tuple[float, float]:
    """Get swap memory usage.

    Returns:
        Tuple of (used_gb, percent_used)

    """
    try:
        import psutil
        swap = psutil.swap_memory()
        return (swap.used / (1024 ** 3), swap.percent)
    except ImportError:
        return (0.0, 0.0)


def get_cpu_count() -> int:
    """Get number of CPU cores.

    Returns:
        Number of CPU cores

    """
    return os.cpu_count() or 4


def get_cpu_temperature() -> Optional[float]:
    """Get CPU temperature in Celsius.

    Returns:
        Temperature in Celsius, or None if not available

    """
    try:
        import psutil
        temps = psutil.sensors_temperatures()

        # Try common sensor names
        for name in ['coretemp', 'k10temp', 'cpu_thermal']:
            if name in temps:
                entries = temps[name]
                if entries:
                    return entries[0].current

        return None
    except (ImportError, AttributeError):
        return None


def get_cpu_frequency() -> Optional[float]:
    """Get current CPU frequency in MHz.

    Returns:
        CPU frequency in MHz, or None if not available

    """
    try:
        import psutil
        freq = psutil.cpu_freq()
        return freq.current if freq else None
    except ImportError:
        return None


def get_hardware_info() -> dict:
    """Get comprehensive hardware information.

    Returns:
        Dictionary of hardware details

    """
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "cpu_cores": get_cpu_count(),
        "total_memory_gb": get_total_memory(),
        "available_memory_gb": get_available_memory()
    }

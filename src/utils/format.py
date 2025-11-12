"""Formatting utilities for display and output.

This module provides utilities for formatting values, progress indicators,
and display output.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def format_bytes(bytes_value: float) -> str:
    """Format bytes as human-readable size.

    Args:
        bytes_value: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 GB", "234 MB")

    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2h 15m", "45s", "1.5s")

    """
    if seconds < 1:
        return f"{seconds:.1f}s"
    elif seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.0f}m {seconds % 60:.0f}s"
    else:
        hours = seconds / 3600
        minutes = (seconds % 3600) / 60
        return f"{hours:.0f}h {minutes:.0f}m"


def format_tokens_per_sec(tps: float) -> str:
    """Format tokens per second with interpretation.

    Args:
        tps: Tokens per second

    Returns:
        Formatted string with interpretation

    """
    if tps < 2:
        interpretation = "very slow"
    elif tps < 5:
        interpretation = "slow but readable"
    elif tps < 10:
        interpretation = "moderate"
    elif tps < 15:
        interpretation = "comfortable"
    elif tps < 20:
        interpretation = "fast"
    elif tps < 30:
        interpretation = "very fast"
    else:
        interpretation = "excellent"

    return f"{tps:.1f} t/s ({interpretation})"


def format_progress(current: int, total: int, width: int = 40) -> str:
    """Format a progress bar.

    Args:
        current: Current progress value
        total: Total value
        width: Width of progress bar in characters

    Returns:
        Formatted progress bar string

    """
    if total == 0:
        percent = 0
    else:
        percent = (current / total) * 100

    filled = int(width * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)

    return f"[{bar}] {percent:.0f}% ({current}/{total})"


def format_table_row(columns: list, widths: list) -> str:
    """Format a table row with aligned columns.

    Args:
        columns: List of column values
        widths: List of column widths

    Returns:
        Formatted row string

    """
    parts = []
    for col, width in zip(columns, widths):
        parts.append(str(col).ljust(width))

    return " ".join(parts)


def colorize(text: str, color: str) -> str:
    """Add ANSI color codes to text (if supported).

    Args:
        text: Text to colorize
        color: Color name (red, green, yellow, blue, etc.)

    Returns:
        Colorized text with ANSI codes

    """
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }

    color_code = colors.get(color.lower(), '')
    reset_code = colors['reset']

    return f"{color_code}{text}{reset_code}" if color_code else text

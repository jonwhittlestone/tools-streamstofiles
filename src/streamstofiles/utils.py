"""Utility functions for file naming and path management."""

import re
from pathlib import Path


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """
    Sanitize a string to be safe for use as a filename.

    Args:
        name: The string to sanitize
        max_length: Maximum length for the resulting filename

    Returns:
        A sanitized filename safe for filesystem use
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[/\\:*?"<>|]', '_', name)

    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')

    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')

    return sanitized


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Returns:
        The path (as a Path object)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_track_number(track_num: int, total_tracks: int) -> str:
    """
    Format a track number with leading zeros based on total track count.

    Args:
        track_num: The track number (1-indexed)
        total_tracks: Total number of tracks in the playlist

    Returns:
        Formatted track number string (e.g., "01", "02", "123")
    """
    # Determine how many digits we need
    digits = len(str(total_tracks))
    return str(track_num).zfill(digits)

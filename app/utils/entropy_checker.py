"""
Entropy Checker — calculates Shannon entropy of file bytes.

High entropy (>7.5) is a strong indicator of encrypted/compressed data,
which may indicate ransomware activity.
"""

from __future__ import annotations

import math
from typing import BinaryIO


def calculate_entropy(data: bytes) -> float:
    """
    Compute the Shannon entropy of a byte sequence.

    Args:
        data: Raw bytes to analyze.

    Returns:
        Float entropy value between 0.0 and 8.0.
    """
    if not data:
        return 0.0

    length = len(data)
    freq = [0] * 256

    for byte in data:
        freq[byte] += 1

    entropy = 0.0
    for count in freq:
        if count == 0:
            continue
        p = count / length
        entropy -= p * math.log2(p)

    return round(entropy, 4)


def calculate_file_entropy(filepath: str, sample_size: int = 10 * 1024 * 1024) -> float:
    """
    Calculate entropy of a file on disk. Reads the whole file
    (or up to sample_size bytes for very large files).

    Args:
        filepath: Path to the file.
        sample_size: Max bytes to read (default 10 MB).

    Returns:
        Float entropy value.
    """
    with open(filepath, "rb") as f:
        data = f.read(sample_size)

    return calculate_entropy(data)


def entropy_risk_label(entropy: float) -> str:
    """
    Return a human-readable label for entropy ranges.
    """
    if entropy >= 7.5:
        return "Very High"
    elif entropy >= 6.5:
        return "High"
    elif entropy >= 5.0:
        return "Medium"
    elif entropy >= 3.0:
        return "Low"
    else:
        return "Very Low"


def is_likely_encrypted(entropy: float, threshold: float = 7.5) -> bool:
    """
    Return True if entropy exceeds the threshold indicating likely encryption.

    Args:
        entropy: Computed entropy value.
        threshold: Entropy threshold (default 7.5).

    Returns:
        True if the file appears to be encrypted.
    """
    return entropy >= threshold


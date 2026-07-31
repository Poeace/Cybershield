"""
Hash Checker — computes SHA-256 hash of files and checks against
known malicious hash databases (including demo ransomware hashes).
"""

from __future__ import annotations

import hashlib
from typing import Set


# Known malicious hashes (demo / educational purposes only).
# In production, this would be sourced from threat intelligence feeds.
KNOWN_MALICIOUS_HASHES: Set[str] = set()


def register_malicious_hash(hash_str: str) -> None:
    """
    Register a SHA-256 hash as known-malicious (used by demo encryptor).
    """
    KNOWN_MALICIOUS_HASHES.add(hash_str.lower())


def unregister_malicious_hash(hash_str: str) -> None:
    """
    Remove a hash from the known-malicious set.
    """
    KNOWN_MALICIOUS_HASHES.discard(hash_str.lower())


def compute_sha256(data: bytes) -> str:
    """
    Compute SHA-256 hex digest of raw bytes.

    Args:
        data: Input bytes.

    Returns:
        Lowercase hex string of the SHA-256 hash.
    """
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(filepath: str, sample_size: int = 100 * 1024 * 1024) -> str:
    """
    Compute SHA-256 of a file on disk. Reads whole file
    (or up to sample_size bytes for very large files).

    Args:
        filepath: Path to the file.
        sample_size: Maximum bytes to read (default 100 MB).

    Returns:
        Lowercase hex SHA-256 hash string.
    """
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)  # 64 KB chunks
            if not chunk:
                break
            sha.update(chunk)
            # Stop reading if we've exceeded the sample size
            if sample_size and f.tell() > sample_size:
                break
    return sha.hexdigest()


def is_known_malicious(file_hash: str) -> bool:
    """
    Check if a SHA-256 hash is in the known malicious set.

    Args:
        file_hash: SHA-256 hex string.

    Returns:
        True if the hash is recognised as malicious.
    """
    return file_hash.lower() in KNOWN_MALICIOUS_HASHES


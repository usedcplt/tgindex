"""Hashing utilities."""

import hashlib


def compute_hash(data: str) -> str:
    """Compute SHA-256 hash of string data."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_url_hash(url: str) -> str:
    """Compute hash for URL deduplication."""
    normalized = url.strip().lower()
    return compute_hash(normalized)

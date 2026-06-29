"""
Recency filter — keep only postings from the last N hours (default 24).
"""

from __future__ import annotations

from typing import List

from ..scrapers.base import JobPosting


def filter_recent(postings: List[JobPosting], hours: int = 24) -> List[JobPosting]:
    """Return postings that were posted within the last *hours* hours."""
    return [p for p in postings if p.is_recent(hours)]

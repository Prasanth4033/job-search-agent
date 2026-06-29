"""
US location filter.
Accepts a JobPosting only if its location field references the United States.
"""

from __future__ import annotations

import re
from typing import List

from ..scrapers.base import JobPosting

# Broad US pattern — catches abbreviations, city names, remote-US
_US_PATTERN = re.compile(
    r"\b("
    r"us|usa|u\.s\.?a?|united\s+states|"
    r"remote|anywhere|"
    # All 50 state abbreviations
    r"al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|"
    r"ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|"
    r"sd|tn|tx|ut|vt|va|wa|wv|wi|wy|dc"
    r")\b",
    re.IGNORECASE,
)

# Explicit non-US country keywords — reject these even if "remote" is mentioned
_NON_US_PATTERN = re.compile(
    r"\b(india|bangalore|bengaluru|hyderabad|pune|mumbai|chennai|"
    r"delhi|noida|gurugram|gurgaon|kolkata|canada|uk|australia|"
    r"singapore|philippines|mexico)\b",
    re.IGNORECASE,
)


def is_us_location(posting: JobPosting) -> bool:
    """Return True if the posting location is in the United States."""
    loc = posting.location or ""
    if _NON_US_PATTERN.search(loc):
        return False
    if _US_PATTERN.search(loc):
        return True
    # If location is empty or ambiguous, include optimistically
    return not loc.strip()


def filter_us_only(postings: List[JobPosting]) -> List[JobPosting]:
    """Return only US-based postings from the list."""
    return [p for p in postings if is_us_location(p)]

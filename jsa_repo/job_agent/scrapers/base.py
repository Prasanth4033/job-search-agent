"""
Abstract base scraper — all site-specific scrapers inherit from this.
Provides shared HTTP session, retry logic, rate-limiting, and the
canonical JobPosting dataclass.
"""

from __future__ import annotations

import time
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlencode, quote_plus

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logger import logger


# ──────────────────────────────────────────────
# Canonical data model
# ──────────────────────────────────────────────

@dataclass
class JobPosting:
    """Normalised job posting returned by every scraper."""
    title: str
    company: str
    location: str
    posted_date: Optional[datetime]
    apply_url: str
    source: str
    skills: List[str] = field(default_factory=list)
    description_snippet: str = ""
    salary: str = "Not specified"
    job_type: str = "Not specified"   # Full-time / Contract / C2C etc.

    def is_recent(self, hours: int = 24) -> bool:
        """Return True if posted within the last *hours* hours."""
        if self.posted_date is None:
            return True   # Unknown date — include optimistically
        delta = datetime.utcnow() - self.posted_date
        return delta.total_seconds() <= hours * 3600

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "posted_date": self.posted_date.isoformat() if self.posted_date else "Unknown",
            "apply_url": self.apply_url,
            "source": self.source,
            "skills": self.skills,
            "description_snippet": self.description_snippet,
            "salary": self.salary,
            "job_type": self.job_type,
        }


# ──────────────────────────────────────────────
# Shared HTTP session factory
# ──────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}


def build_session(retries: int = 3, backoff: float = 1.5) -> requests.Session:
    """Return a requests Session with retry/backoff wired in."""
    session = requests.Session()
    session.headers.update(HEADERS)
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# ──────────────────────────────────────────────
# Abstract base
# ──────────────────────────────────────────────

class BaseScraper(ABC):
    """
    Base class for all job-board scrapers.

    Subclasses must implement:
      - ``scrape(query: str) -> List[JobPosting]``

    They may optionally override:
      - ``search_url(query)``   — build the search URL
      - ``parse(response, query)`` — parse an HTTP response into postings
    """

    SOURCE_NAME: str = "Unknown"
    BASE_URL: str = ""
    REQUEST_DELAY_RANGE: tuple = (1.5, 3.5)   # polite crawl delay (seconds)
    TIMEOUT: int = 15

    def __init__(self):
        self.session = build_session()
        self._last_request_time: float = 0.0

    # ── helpers ──────────────────────────────

    def _throttle(self) -> None:
        """Enforce a polite delay between consecutive requests."""
        delay = random.uniform(*self.REQUEST_DELAY_RANGE)
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)

    def _get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """GET with throttling, error handling and logging."""
        self._throttle()
        try:
            resp = self.session.get(url, timeout=self.TIMEOUT, **kwargs)
            self._last_request_time = time.monotonic()
            resp.raise_for_status()
            logger.debug(f"[{self.SOURCE_NAME}] GET {url} → {resp.status_code}")
            return resp
        except requests.exceptions.HTTPError as e:
            logger.warning(f"[{self.SOURCE_NAME}] HTTP error for {url}: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"[{self.SOURCE_NAME}] Connection error: {e}")
        except requests.exceptions.Timeout:
            logger.warning(f"[{self.SOURCE_NAME}] Timeout for {url}")
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] Unexpected error: {e}")
        return None

    @staticmethod
    def _encode_query(query: str) -> str:
        return quote_plus(query)

    # ── interface ────────────────────────────

    @abstractmethod
    def scrape(self, query: str) -> List[JobPosting]:
        """Fetch job postings for *query* and return normalised list."""
        ...

    def scrape_all_skills(self, skill_queries: List[str]) -> List[JobPosting]:
        """
        Iterate over multiple skill queries, deduplicate by URL,
        and return all postings found.
        """
        seen_urls: set = set()
        results: List[JobPosting] = []

        for query in skill_queries:
            logger.info(f"[{self.SOURCE_NAME}] Searching: {query!r}")
            try:
                postings = self.scrape(query)
                for p in postings:
                    if p.apply_url not in seen_urls:
                        seen_urls.add(p.apply_url)
                        results.append(p)
            except Exception as e:
                logger.error(f"[{self.SOURCE_NAME}] Failed on query {query!r}: {e}")

        logger.info(f"[{self.SOURCE_NAME}] Total unique postings: {len(results)}")
        return results

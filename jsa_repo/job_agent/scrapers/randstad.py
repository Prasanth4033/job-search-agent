"""
Randstad USA scraper.
Target: https://www.randstadusa.com/jobs/q-{query}/l-united-states/
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, JobPosting
from ..utils.logger import logger


class RandstadScraper(BaseScraper):

    SOURCE_NAME = "Randstad USA"
    BASE_URL = "https://www.randstadusa.com"

    def search_url(self, query: str) -> str:
        q = self._encode_query(query)
        return f"{self.BASE_URL}/jobs/q-{q}/l-united-states/"

    # ── date parsing ─────────────────────────

    @staticmethod
    def _parse_date(text: str) -> Optional[datetime]:
        """Convert relative ('2 hours ago', 'Today') or absolute dates."""
        if not text:
            return None
        t = text.strip().lower()

        if "just now" in t or "today" in t or "minute" in t:
            return datetime.utcnow()
        m = re.search(r"(\d+)\s+hour", t)
        if m:
            return datetime.utcnow() - timedelta(hours=int(m.group(1)))
        m = re.search(r"(\d+)\s+day", t)
        if m:
            return datetime.utcnow() - timedelta(days=int(m.group(1)))

        # Try absolute: "Jun 29, 2025"
        for fmt in ("%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(t, fmt)
            except ValueError:
                pass
        return None

    # ── parsing ──────────────────────────────

    def parse(self, html: str, query: str) -> List[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        postings: List[JobPosting] = []

        # Randstad wraps each job in <article> or <li> with class containing "job"
        cards = (
            soup.find_all("article", class_=re.compile(r"job", re.I))
            or soup.find_all("li", attrs={"data-job-id": True})
            or soup.select(".job-card, .jobs-card, [class*='jobCard']")
        )

        if not cards:
            logger.debug(f"[{self.SOURCE_NAME}] No job cards found for {query!r} — page structure may have changed.")

        for card in cards:
            try:
                # Title
                title_el = (
                    card.find("h2") or card.find("h3")
                    or card.find(class_=re.compile(r"title", re.I))
                )
                title = title_el.get_text(strip=True) if title_el else "Unknown Title"

                # Location
                loc_el = card.find(class_=re.compile(r"location", re.I))
                location = loc_el.get_text(strip=True) if loc_el else "United States"

                # Date
                date_el = card.find(class_=re.compile(r"date|posted|time", re.I))
                posted_date = self._parse_date(date_el.get_text(strip=True) if date_el else "")

                # URL
                link_el = card.find("a", href=True)
                url = urljoin(self.BASE_URL, link_el["href"]) if link_el else self.BASE_URL

                # Snippet
                snippet_el = card.find(class_=re.compile(r"desc|snippet|summary", re.I))
                snippet = snippet_el.get_text(strip=True)[:300] if snippet_el else ""

                postings.append(JobPosting(
                    title=title,
                    company="Randstad USA (Client Confidential)",
                    location=location,
                    posted_date=posted_date,
                    apply_url=url,
                    source=self.SOURCE_NAME,
                    skills=[query],
                    description_snippet=snippet,
                ))
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] Card parse error: {e}")

        return postings

    # ── public interface ─────────────────────

    def scrape(self, query: str) -> List[JobPosting]:
        url = self.search_url(query)
        resp = self._get(url)
        if resp is None:
            logger.warning(f"[{self.SOURCE_NAME}] No response for {url}")
            return []
        return self.parse(resp.text, query)

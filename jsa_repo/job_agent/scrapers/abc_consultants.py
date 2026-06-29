"""
ABC Consultants scraper.
NOTE: ABC Consultants is India-based. US job volume is very limited.
      This scraper filters strictly to US-labelled postings only.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, JobPosting
from ..utils.logger import logger

_US_PATTERN = re.compile(
    r"\b(usa|united\s+states|u\.s\.a|remote\s*\(us\)|us\s+remote)\b", re.IGNORECASE
)


class ABCConsultantsScraper(BaseScraper):

    SOURCE_NAME = "ABC Consultants"
    BASE_URL = "https://www.abcconsultants.com"

    def search_url(self, query: str) -> str:
        q = self._encode_query(query)
        return f"{self.BASE_URL}/jobs?q={q}&location=United+States&country=US"

    @staticmethod
    def _parse_date(raw: str) -> Optional[datetime]:
        if not raw:
            return None
        raw = raw.strip().lower()
        if "today" in raw or "just now" in raw:
            return datetime.utcnow()
        m = re.search(r"(\d+)\s+hour", raw)
        if m:
            return datetime.utcnow() - timedelta(hours=int(m.group(1)))
        m = re.search(r"(\d+)\s+day", raw)
        if m:
            return datetime.utcnow() - timedelta(days=int(m.group(1)))
        return None

    def parse(self, html: str, query: str) -> List[JobPosting]:
        soup = BeautifulSoup(html, "html.parser")
        postings: List[JobPosting] = []

        cards = soup.select(
            ".job-card, .job-item, .job-listing, "
            "article.job, [class*='job-card'], [class*='jobCard']"
        )

        for card in cards:
            try:
                title_el  = card.find(["h2", "h3", "h4"]) or card.find(class_=re.compile(r"title", re.I))
                title     = title_el.get_text(strip=True) if title_el else "Unknown"
                loc_el    = card.find(class_=re.compile(r"location|city", re.I))
                location  = loc_el.get_text(strip=True) if loc_el else ""

                # Strict US filter — skip India/other locations
                if location and not _US_PATTERN.search(location):
                    continue

                link_el   = card.find("a", href=True)
                job_url   = urljoin(self.BASE_URL, link_el["href"]) if link_el else self.BASE_URL
                date_el   = card.find(class_=re.compile(r"date|posted|time", re.I))
                posted    = self._parse_date(date_el.get_text(strip=True) if date_el else "")
                snippet_el = card.find(class_=re.compile(r"desc|summary|detail", re.I))
                snippet   = snippet_el.get_text(strip=True)[:300] if snippet_el else ""

                postings.append(JobPosting(
                    title=title,
                    company="ABC Consultants (Client Confidential)",
                    location=location or "United States",
                    posted_date=posted,
                    apply_url=job_url,
                    source=self.SOURCE_NAME,
                    skills=[query],
                    description_snippet=snippet,
                ))
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] Card parse error: {e}")

        return postings

    def scrape(self, query: str) -> List[JobPosting]:
        url = self.search_url(query)
        resp = self._get(url)
        if resp is None:
            logger.warning(
                f"[{self.SOURCE_NAME}] Could not reach site. "
                "Note: ABC Consultants is India-based; US listings are very limited."
            )
            return []
        return self.parse(resp.text, query)

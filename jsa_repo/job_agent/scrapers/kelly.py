"""
Kelly Services scraper.
Kelly uses Phenom People ATS (JavaScript SPA), so direct HTML parsing
often returns an empty shell. This module tries the JSON search API
endpoint that the SPA calls, then falls back to the public sitemap feed.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, JobPosting
from ..utils.logger import logger


class KellyScraper(BaseScraper):

    SOURCE_NAME = "Kelly Services"
    BASE_URL = "https://jobs.kellyservices.com"
    # Phenom People search API used by the SPA
    API_URL = "https://jobs.kellyservices.com/api/jobs"

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
        try:
            return datetime.fromisoformat(raw.replace("z", ""))
        except ValueError:
            pass
        return None

    # ── JSON API path ─────────────────────────

    def _scrape_via_api(self, query: str) -> List[JobPosting]:
        params = {
            "keywords": query,
            "country": "us",
            "pageSize": 50,
            "page": 0,
            "sortBy": "postedDate",
            "sortOrder": "desc",
        }
        resp = self._get(
            self.API_URL,
            params=params,
            headers={"Accept": "application/json"},
        )
        if resp is None:
            return []
        try:
            data = resp.json()
        except ValueError:
            return []

        postings: List[JobPosting] = []
        jobs = data.get("jobs") or data.get("data", {}).get("jobs", [])
        for job in jobs:
            title    = job.get("title", "Unknown")
            location = job.get("location", {})
            if isinstance(location, dict):
                city  = location.get("city", "")
                state = location.get("state", "")
                location = f"{city}, {state}".strip(", ")
            else:
                location = str(location)

            date_raw  = job.get("postedDate") or job.get("datePosted", "")
            job_id    = job.get("id") or job.get("jobId", "")
            job_url   = job.get("applyUrl") or f"{self.BASE_URL}/us/en/job/{job_id}"
            snippet   = job.get("description", "")[:300]
            job_type  = job.get("employmentType", "Not specified")

            postings.append(JobPosting(
                title=title,
                company="Kelly Services (Client Confidential)",
                location=location,
                posted_date=self._parse_date(str(date_raw)),
                apply_url=job_url,
                source=self.SOURCE_NAME,
                skills=[query],
                description_snippet=snippet,
                job_type=job_type,
            ))
        return postings

    # ── RSS/sitemap fallback ─────────────────

    def _scrape_via_rss(self, query: str) -> List[JobPosting]:
        q = self._encode_query(query)
        url = f"{self.BASE_URL}/us/en/search-results?keywords={q}&country=us"
        resp = self._get(url)
        if resp is None:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        postings: List[JobPosting] = []

        for card in soup.select(
            "[data-ph-at-id='jobs-list-item'], .job-card, "
            "[class*='JobCard'], [class*='job-card'], article"
        ):
            try:
                title_el  = card.find(["h2", "h3"]) or card.find(attrs={"data-ph-at-id": "job-title"})
                title     = title_el.get_text(strip=True) if title_el else "Unknown"
                link_el   = card.find("a", href=True)
                job_url   = urljoin(self.BASE_URL, link_el["href"]) if link_el else url
                loc_el    = card.find(class_=re.compile(r"location", re.I))
                location  = loc_el.get_text(strip=True) if loc_el else "United States"
                date_el   = card.find(class_=re.compile(r"date|posted|time", re.I))
                posted    = self._parse_date(date_el.get_text(strip=True) if date_el else "")

                postings.append(JobPosting(
                    title=title,
                    company="Kelly Services (Client Confidential)",
                    location=location,
                    posted_date=posted,
                    apply_url=job_url,
                    source=self.SOURCE_NAME,
                    skills=[query],
                ))
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] Card parse error: {e}")

        return postings

    # ── public interface ──────────────────────

    def scrape(self, query: str) -> List[JobPosting]:
        results = self._scrape_via_api(query)
        if not results:
            logger.debug(f"[{self.SOURCE_NAME}] API returned 0 — trying HTML fallback.")
            results = self._scrape_via_rss(query)
        return results

"""
ManpowerGroup USA scraper.
Target: https://www.manpower.com/ManpowerUSA/JobSearch/
Uses JSON API endpoint that backs the job search widget.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import List, Optional

from bs4 import BeautifulSoup

from .base import BaseScraper, JobPosting
from ..utils.logger import logger


class ManpowerScraper(BaseScraper):

    SOURCE_NAME = "ManpowerGroup"
    BASE_URL = "https://www.manpower.com"
    # Manpower exposes a lightweight JSON search API
    API_URL = "https://www.manpower.com/ManpowerUSA/api/jobs/search"

    def _api_payload(self, query: str) -> dict:
        return {
            "keyword": query,
            "location": "United States",
            "radius": 50,
            "page": 1,
            "pageSize": 50,
            "sortBy": "datePosted",
            "sortOrder": "desc",
        }

    @staticmethod
    def _parse_date(raw: str) -> Optional[datetime]:
        if not raw:
            return None
        raw = raw.strip().lower()
        if "today" in raw or "just now" in raw or "hour" in raw:
            m = re.search(r"(\d+)\s+hour", raw)
            return datetime.utcnow() - timedelta(hours=int(m.group(1))) if m else datetime.utcnow()
        m = re.search(r"(\d+)\s+day", raw)
        if m:
            return datetime.utcnow() - timedelta(days=int(m.group(1)))
        # ISO string from API
        try:
            return datetime.fromisoformat(raw.replace("z", "+00:00"))
        except ValueError:
            pass
        return None

    # ── JSON API path ────────────────────────

    def _scrape_via_api(self, query: str) -> List[JobPosting]:
        resp = self._get(
            self.API_URL,
            params=self._api_payload(query),
            headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
        )
        if resp is None:
            return []
        try:
            data = resp.json()
        except ValueError:
            return []

        postings: List[JobPosting] = []
        for job in data.get("jobs", data.get("results", [])):
            title      = job.get("title") or job.get("jobTitle", "Unknown")
            location   = job.get("location") or job.get("city", "") + ", " + job.get("state", "")
            date_raw   = job.get("datePosted") or job.get("postedDate", "")
            url        = job.get("url") or f"{self.BASE_URL}/ManpowerUSA/Jobs/{job.get('id', '')}"
            snippet    = job.get("description", "")[:300]
            job_type   = job.get("employmentType", "Not specified")

            postings.append(JobPosting(
                title=title,
                company="ManpowerGroup (Client Confidential)",
                location=location,
                posted_date=self._parse_date(str(date_raw)),
                apply_url=url,
                source=self.SOURCE_NAME,
                skills=[query],
                description_snippet=snippet,
                job_type=job_type,
            ))
        return postings

    # ── HTML fallback ────────────────────────

    def _scrape_via_html(self, query: str) -> List[JobPosting]:
        q = self._encode_query(query)
        url = f"{self.BASE_URL}/ManpowerUSA/JobSearch/?keyword={q}&location=United+States"
        resp = self._get(url)
        if resp is None:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        postings: List[JobPosting] = []

        for card in soup.select(".job-card, .job-listing, [data-job-id], article"):
            try:
                title_el = card.find(["h2", "h3", "h4"]) or card.find(class_=re.compile("title", re.I))
                title    = title_el.get_text(strip=True) if title_el else "Unknown"
                link_el  = card.find("a", href=True)
                job_url  = link_el["href"] if link_el else url
                if not job_url.startswith("http"):
                    job_url = self.BASE_URL + job_url
                loc_el   = card.find(class_=re.compile("location|city", re.I))
                location = loc_el.get_text(strip=True) if loc_el else "United States"
                date_el  = card.find(class_=re.compile("date|posted", re.I))
                posted   = self._parse_date(date_el.get_text(strip=True) if date_el else "")

                postings.append(JobPosting(
                    title=title,
                    company="ManpowerGroup (Client Confidential)",
                    location=location,
                    posted_date=posted,
                    apply_url=job_url,
                    source=self.SOURCE_NAME,
                    skills=[query],
                ))
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] Card parse error: {e}")

        return postings

    # ── public interface ─────────────────────

    def scrape(self, query: str) -> List[JobPosting]:
        # Try JSON API first, fall back to HTML parsing
        results = self._scrape_via_api(query)
        if not results:
            logger.debug(f"[{self.SOURCE_NAME}] API returned 0 results — trying HTML fallback.")
            results = self._scrape_via_html(query)
        return results

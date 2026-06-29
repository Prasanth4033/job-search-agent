"""
CyberCoders scraper — v2.
CyberCoders is a tech-focused US staffing firm with strong DE coverage.
Uses their public HTML job search page.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, JobPosting
from ..utils.logger import logger


class CyberCodersScraper(BaseScraper):

    SOURCE_NAME = "CyberCoders"
    BASE_URL    = "https://www.cybercoders.com"
    SEARCH_URL  = "https://www.cybercoders.com/search/"

    @staticmethod
    def _parse_date(text: str) -> Optional[datetime]:
        if not text:
            return None
        t = text.strip().lower()
        if "today" in t or "just now" in t or "hour" in t:
            m = re.search(r"(\d+)\s+hour", t)
            return datetime.utcnow() - timedelta(hours=int(m.group(1))) if m else datetime.utcnow()
        m = re.search(r"(\d+)\s+day", t)
        if m:
            return datetime.utcnow() - timedelta(days=int(m.group(1)))
        for fmt in ("%b %d, %Y", "%B %d, %Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(t, fmt)
            except ValueError:
                pass
        return None

    def scrape(self, query: str) -> List[JobPosting]:
        params = {
            "searchterms": query,
            "location":    "United States",
            "radius":      25,
            "remote":      "true",
            "orderby":     "relevance",
        }
        resp = self._get(self.SEARCH_URL, params=params)
        if resp is None:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        postings: List[JobPosting] = []

        job_listings = soup.select(".job-listing-item, .job-listing, [class*='job-listing']")
        if not job_listings:
            # Try alternate selectors
            job_listings = soup.select("article, .job-result, [class*='JobCard']")

        for card in job_listings:
            try:
                title_el = card.find(["h2", "h3", "h4"]) or card.find(class_=re.compile(r"title|job-title", re.I))
                title    = title_el.get_text(strip=True) if title_el else "Unknown"

                link_el  = card.find("a", href=True)
                href     = link_el["href"] if link_el else ""
                url      = urljoin(self.BASE_URL, href) if href else self.BASE_URL

                loc_el   = card.find(class_=re.compile(r"location|city", re.I))
                location = loc_el.get_text(strip=True) if loc_el else "United States"

                sal_el   = card.find(class_=re.compile(r"salary|pay|comp", re.I))
                salary   = sal_el.get_text(strip=True) if sal_el else "Not specified"

                date_el  = card.find(class_=re.compile(r"date|posted|time", re.I))
                posted   = self._parse_date(date_el.get_text(strip=True) if date_el else "")

                skill_els = card.select(".skill-tag, .tag, [class*='skill']")
                skills    = [s.get_text(strip=True) for s in skill_els] or [query]

                snippet_el = card.find(class_=re.compile(r"desc|summary|snippet", re.I))
                snippet    = snippet_el.get_text(strip=True)[:300] if snippet_el else ""

                postings.append(JobPosting(
                    title=title,
                    company="CyberCoders (Client Confidential)",
                    location=location,
                    posted_date=posted,
                    apply_url=url,
                    source=self.SOURCE_NAME,
                    skills=skills,
                    description_snippet=snippet,
                    salary=salary,
                ))
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] Card parse error: {e}")

        logger.info(f"[{self.SOURCE_NAME}] {len(postings)} postings for {query!r}")
        return postings

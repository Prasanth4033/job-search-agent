"""
Dice.com scraper — v2.1
The private JSON API (dhigroupinc.com) returns 403 for unauthenticated requests.
This version scrapes Dice's public HTML search results page instead.
Dice embeds job data as JSON inside a <script id="__NEXT_DATA__"> tag.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urljoin, quote_plus

from bs4 import BeautifulSoup

from .base import BaseScraper, JobPosting
from ..utils.logger import logger


class DiceScraper(BaseScraper):

    SOURCE_NAME = "Dice"
    BASE_URL    = "https://www.dice.com"
    SEARCH_URL  = "https://www.dice.com/jobs"

    @staticmethod
    def _parse_date(raw: str) -> Optional[datetime]:
        if not raw:
            return None
        raw = raw.strip().lower()
        if "just now" in raw or "today" in raw:
            return datetime.utcnow()
        m = re.search(r"(\d+)\s+hour", raw)
        if m:
            return datetime.utcnow() - timedelta(hours=int(m.group(1)))
        m = re.search(r"(\d+)\s+day", raw)
        if m:
            return datetime.utcnow() - timedelta(days=int(m.group(1)))
        try:
            return datetime.fromisoformat(raw[:19].replace("z", ""))
        except ValueError:
            pass
        return None

    @staticmethod
    def _extract_from_dehydrated(props: dict) -> list:
        """
        Dice uses React Query — job results live inside dehydratedState.queries[].state.data.
        Walk all queries and collect anything that looks like a job list.
        """
        jobs: list = []
        dh = props.get("dehydratedState", {})
        for query_entry in dh.get("queries", []):
            data = query_entry.get("state", {}).get("data", {})
            # data may be the jobs array directly or nested
            if isinstance(data, list):
                jobs.extend(data)
            elif isinstance(data, dict):
                for val in data.values():
                    if isinstance(val, list) and val and isinstance(val[0], dict) and ("title" in val[0] or "jobTitle" in val[0]):
                        jobs.extend(val)
                    elif isinstance(val, dict):
                        for inner_val in val.values():
                            if isinstance(inner_val, list) and inner_val and isinstance(inner_val[0], dict):
                                if "title" in inner_val[0] or "jobTitle" in inner_val[0]:
                                    jobs.extend(inner_val)
        return jobs

    def _parse_next_data(self, html: str, query: str) -> List[JobPosting]:
        """Extract jobs from Next.js __NEXT_DATA__ JSON embedded in page."""
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            logger.debug(f"[{self.SOURCE_NAME}] No __NEXT_DATA__ script tag found.")
            return []

        try:
            nd = json.loads(script.string)
        except (json.JSONDecodeError, TypeError):
            return []

        # Navigate to jobs list — Dice uses multiple structures across versions
        props = nd.get("props", {}).get("pageProps", {})
        jobs = (
            # Legacy / older Dice Next.js versions
            props.get("initialState", {}).get("jobs", {}).get("jobs", [])
            # Direct pageProps.jobs
            or props.get("jobs", [])
            # Search results wrapper
            or props.get("searchResults", {}).get("jobs", [])
            or props.get("searchResults", {}).get("results", [])
            # data.jobs
            or props.get("data", {}).get("jobs", [])
            # React Query dehydrated state (current Dice)
            or self._extract_from_dehydrated(props)
            or []
        )
        logger.debug(f"[{self.SOURCE_NAME}] __NEXT_DATA__ jobs found: {len(jobs)} for {query!r}")

        postings: List[JobPosting] = []
        for job in jobs:
            title      = job.get("title") or job.get("jobTitle", "Unknown")
            company    = job.get("advertiser", {}).get("name", "") or job.get("company", "Company Confidential")
            if isinstance(company, dict):
                company = company.get("name", "Company Confidential")
            location   = job.get("location", "United States")
            if isinstance(location, dict):
                location = location.get("displayName", "United States")
            date_raw   = job.get("postedDate") or job.get("date", "")
            job_id     = job.get("id") or job.get("jobId", "")
            url        = job.get("applyUrl") or (f"{self.BASE_URL}/job-detail/{job_id}" if job_id else self.BASE_URL)
            snippet    = job.get("summary") or job.get("jobDescription", "")
            snippet    = snippet[:400] if snippet else ""
            salary     = str(job.get("salary") or job.get("pay", "Not specified"))
            job_type   = str(job.get("employmentType") or job.get("jobType", "Not specified"))
            skills     = job.get("skills") or [query]
            if not isinstance(skills, list):
                skills = [query]

            postings.append(JobPosting(
                title=title,
                company=str(company),
                location=str(location),
                posted_date=self._parse_date(str(date_raw)),
                apply_url=url,
                source=self.SOURCE_NAME,
                skills=skills,
                description_snippet=snippet,
                salary=salary,
                job_type=job_type,
                full_description=job.get("jobDescription", snippet),
            ))

        return postings

    def _parse_html_cards(self, html: str, query: str, base_url: str) -> List[JobPosting]:
        """Fallback: parse visible job cards from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        cards = (
            soup.select("dhi-search-card, [data-cy='card-title-link']")
            or soup.select(".card, .job-card, [class*='jobCard'], article")
        )
        postings: List[JobPosting] = []
        for card in cards:
            try:
                title_el = card.find(["h2", "h3", "a"], attrs={"data-cy": "card-title-link"}) or card.find(["h2", "h3"])
                title    = title_el.get_text(strip=True) if title_el else "Unknown"
                link_el  = card.find("a", href=True)
                href     = link_el["href"] if link_el else ""
                url      = urljoin(self.BASE_URL, href) if href else base_url
                loc_el   = card.find(attrs={"data-cy": "search-result-location"}) or card.find(class_=re.compile(r"location", re.I))
                location = loc_el.get_text(strip=True) if loc_el else "United States"
                date_el  = card.find(attrs={"data-cy": "card-posted-date"}) or card.find(class_=re.compile(r"date|posted", re.I))
                posted   = self._parse_date(date_el.get_text(strip=True) if date_el else "")
                comp_el  = card.find(attrs={"data-cy": "search-result-company-name"}) or card.find(class_=re.compile(r"company", re.I))
                company  = comp_el.get_text(strip=True) if comp_el else "Company Confidential"
                postings.append(JobPosting(
                    title=title,
                    company=company,
                    location=location,
                    posted_date=posted,
                    apply_url=url,
                    source=self.SOURCE_NAME,
                    skills=[query],
                ))
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] Card parse error: {e}")
        return postings

    def scrape(self, query: str) -> List[JobPosting]:
        q    = quote_plus(query)
        url  = f"{self.SEARCH_URL}?q={q}&countryCode=US&radius=30&radiusUnit=mi&page=1&pageSize=50&filters.postedDate=ONE&language=en"
        resp = self._get(url, headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        if resp is None:
            return []

        # Try Next.js embedded data first
        postings = self._parse_next_data(resp.text, query)
        if not postings:
            logger.debug(f"[{self.SOURCE_NAME}] No __NEXT_DATA__ jobs — trying HTML cards.")
            postings = self._parse_html_cards(resp.text, query, url)

        logger.info(f"[{self.SOURCE_NAME}] {len(postings)} postings for {query!r}")
        return postings

"""
Randstad USA scraper — v2.
Randstad is a React SPA; direct HTML page fetches return a JS shell with no
job cards. This scraper calls the internal JSON search API that the SPA itself
uses, so results are always live and accurate.

Fallback: if the API returns nothing, we attempt the listing HTML page and
look for any server-side-rendered job data embedded as JSON in a <script> tag.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseScraper, JobPosting
from ..utils.logger import logger


class RandstadScraper(BaseScraper):

    SOURCE_NAME = "Randstad USA"
    BASE_URL    = "https://www.randstadusa.com"
    # Internal JSON API used by the React SPA
    API_URL     = "https://www.randstadusa.com/api/jobs/search"

    # ── date helpers ─────────────────────────

    @staticmethod
    def _parse_date(text: str) -> Optional[datetime]:
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
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(t[:19], fmt)
            except ValueError:
                pass
        return None

    # ── JSON API path ─────────────────────────

    def _api_payload(self, query: str) -> dict:
        return {
            "keyword":  query,
            "location": "United States",
            "radius":   50,
            "pageSize": 50,
            "page":     1,
            "sortBy":   "datePosted",
            "sortOrder": "desc",
        }

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
        jobs = (
            data.get("jobs")
            or data.get("results")
            or data.get("data", {}).get("jobs", [])
            or []
        )
        for job in jobs:
            title      = job.get("title") or job.get("jobTitle", "Unknown")
            city       = job.get("city") or job.get("location", {}).get("city", "")
            state      = job.get("state") or job.get("location", {}).get("state", "")
            location   = f"{city}, {state}".strip(", ") or "United States"
            date_raw   = job.get("datePosted") or job.get("postedDate", "")
            job_id     = job.get("id") or job.get("jobId", "")
            slug       = job.get("slug") or job.get("urlSlug", "")
            url        = (
                job.get("url")
                or (f"{self.BASE_URL}/jobs/4/{job_id}/{slug}/" if job_id else self.BASE_URL)
            )
            snippet    = job.get("description", "")[:400]
            salary     = job.get("salary") or job.get("payRate", "Not specified")
            job_type   = job.get("employmentType") or job.get("jobType", "Contract")
            spoc       = job.get("recruiter") or job.get("contactName", "")
            spoc_email = job.get("recruiterEmail") or job.get("contactEmail", "")

            postings.append(JobPosting(
                title=title,
                company="Randstad Digital (Client Confidential)",
                location=location,
                posted_date=self._parse_date(str(date_raw)),
                apply_url=url,
                source=self.SOURCE_NAME,
                skills=[query],
                description_snippet=snippet,
                salary=str(salary),
                job_type=job_type,
                spoc_name=spoc,
                spoc_email=spoc_email,
                full_description=job.get("fullDescription", snippet),
            ))
        return postings

    # ── HTML/JSON-in-script fallback ──────────

    def _scrape_via_listing_page(self, query: str) -> List[JobPosting]:
        """
        Try the listing page URL. Randstad sometimes embeds job data as
        a JSON blob inside a <script id="__NEXT_DATA__"> tag.
        """
        q   = self._encode_query(query)
        url = f"{self.BASE_URL}/jobs/q-{q}/l-united-states/"
        resp = self._get(url)
        if resp is None:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # 1) Try Next.js embedded JSON
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if script_tag:
            try:
                nd    = json.loads(script_tag.string)
                props = nd.get("props", {}).get("pageProps", {})
                jobs  = (
                    props.get("jobs")
                    or props.get("initialJobs")
                    or props.get("jobListings", [])
                )
                if jobs:
                    postings = []
                    for job in jobs:
                        title    = job.get("title", "Unknown")
                        location = job.get("location") or job.get("city", "United States")
                        date_raw = job.get("datePosted") or job.get("posted", "")
                        href     = job.get("url") or job.get("slug", "")
                        job_url  = urljoin(self.BASE_URL, href) if href else url
                        snippet  = job.get("description", "")[:400]
                        postings.append(JobPosting(
                            title=title,
                            company="Randstad Digital (Client Confidential)",
                            location=location,
                            posted_date=self._parse_date(str(date_raw)),
                            apply_url=job_url,
                            source=self.SOURCE_NAME,
                            skills=[query],
                            description_snippet=snippet,
                        ))
                    return postings
            except (json.JSONDecodeError, AttributeError):
                pass

        # 2) Try plain HTML job cards
        cards = (
            soup.find_all("article", class_=re.compile(r"job", re.I))
            or soup.find_all("li", attrs={"data-job-id": True})
            or soup.select(".job-card, .jobs-card, [class*='jobCard']")
        )
        postings = []
        for card in cards:
            try:
                title_el = card.find("h2") or card.find("h3") or card.find(class_=re.compile(r"title", re.I))
                title    = title_el.get_text(strip=True) if title_el else "Unknown Title"
                loc_el   = card.find(class_=re.compile(r"location", re.I))
                location = loc_el.get_text(strip=True) if loc_el else "United States"
                date_el  = card.find(class_=re.compile(r"date|posted|time", re.I))
                posted   = self._parse_date(date_el.get_text(strip=True) if date_el else "")
                link_el  = card.find("a", href=True)
                job_url  = urljoin(self.BASE_URL, link_el["href"]) if link_el else self.BASE_URL
                snippet_el = card.find(class_=re.compile(r"desc|snippet|summary", re.I))
                snippet  = snippet_el.get_text(strip=True)[:300] if snippet_el else ""
                postings.append(JobPosting(
                    title=title,
                    company="Randstad Digital (Client Confidential)",
                    location=location,
                    posted_date=posted,
                    apply_url=job_url,
                    source=self.SOURCE_NAME,
                    skills=[query],
                    description_snippet=snippet,
                ))
            except Exception as e:
                logger.debug(f"[{self.SOURCE_NAME}] Card parse error: {e}")

        if not postings:
            logger.debug(f"[{self.SOURCE_NAME}] No job cards found for {query!r} — Randstad SPA may have changed structure.")

        return postings

    # ── public interface ─────────────────────

    def scrape(self, query: str) -> List[JobPosting]:
        results = self._scrape_via_api(query)
        if not results:
            logger.debug(f"[{self.SOURCE_NAME}] JSON API returned 0 — trying listing page fallback.")
            results = self._scrape_via_listing_page(query)
        return results

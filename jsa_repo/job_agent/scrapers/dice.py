"""
Dice.com scraper — v2.
Uses the Dice public job search API (same endpoint the website calls).
Dice is tech-focused and has strong DE/SQL/AWS coverage.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import List, Optional

from .base import BaseScraper, JobPosting
from ..utils.logger import logger


class DiceScraper(BaseScraper):

    SOURCE_NAME = "Dice"
    BASE_URL    = "https://www.dice.com"
    API_URL     = "https://job-search-api.svc.dhigroupinc.com/v1/dice/jobs/search"

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
        # ISO 8601
        try:
            return datetime.fromisoformat(raw[:19].replace("z", ""))
        except ValueError:
            pass
        return None

    def _api_params(self, query: str) -> dict:
        return {
            "q":               query,
            "countryCode2":    "US",
            "radius":          30,
            "radiusUnit":      "mi",
            "page":            1,
            "pageSize":        50,
            "facets":          "employmentType|postedDate|workplaceTypes|employerType",
            "filters.postedDate": "ONE",       # posted in last 24 h
            "filters.workplaceTypes": "Remote|Hybrid|On-site",
            "sort":            "-score",
            "fields":          "id,guid,title,company,employmentType,workplaceTypes,postedDate,modifiedDate,location,salary,skills,summary,applyDataList,recruiterEmail,recruiterName,recruiterPhone",
            "culture":         "en",
        }

    def scrape(self, query: str) -> List[JobPosting]:
        resp = self._get(
            self.API_URL,
            params=self._api_params(query),
            headers={"Accept": "application/json"},
        )
        if resp is None:
            return []
        try:
            data = resp.json()
        except ValueError:
            return []

        postings: List[JobPosting] = []
        for job in data.get("data", []):
            title    = job.get("title", "Unknown")
            company  = job.get("company", {})
            company  = company.get("name", "Company Confidential") if isinstance(company, dict) else str(company)
            location = job.get("location", "United States")
            if isinstance(location, dict):
                location = f"{location.get('displayName', 'United States')}"
            date_raw = job.get("postedDate") or job.get("modifiedDate", "")
            job_id   = job.get("id") or job.get("guid", "")
            url      = f"https://www.dice.com/job-detail/{job_id}" if job_id else self.BASE_URL
            snippet  = job.get("summary", "")[:400]
            salary   = job.get("salary", "Not specified") or "Not specified"
            job_type = job.get("employmentType", "Not specified")
            skills   = job.get("skills", []) or [query]

            # SPOC
            spoc_name  = job.get("recruiterName", "")
            spoc_email = job.get("recruiterEmail", "")
            spoc_phone = job.get("recruiterPhone", "")

            # Apply URL — Dice may have direct apply links
            apply_list = job.get("applyDataList", [])
            if apply_list and isinstance(apply_list, list):
                apply_url = apply_list[0].get("applyUrl", url) or url
            else:
                apply_url = url

            postings.append(JobPosting(
                title=title,
                company=company,
                location=location,
                posted_date=self._parse_date(str(date_raw)),
                apply_url=apply_url,
                source=self.SOURCE_NAME,
                skills=skills if isinstance(skills, list) else [query],
                description_snippet=snippet,
                salary=str(salary),
                job_type=str(job_type),
                spoc_name=spoc_name,
                spoc_email=spoc_email,
                spoc_phone=spoc_phone,
                full_description=job.get("description", snippet),
            ))

        logger.info(f"[{self.SOURCE_NAME}] {len(postings)} postings for {query!r}")
        return postings

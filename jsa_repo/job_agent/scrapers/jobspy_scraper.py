"""
Multi-source scraper using python-jobspy.
Covers: LinkedIn, Indeed, ZipRecruiter, Glassdoor.
jobspy handles anti-bot logic for these sites internally.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import List, Optional

from .base import JobPosting
from ..utils.logger import logger

try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False
    logger.warning("python-jobspy not installed. LinkedIn/Indeed/ZipRecruiter/Glassdoor scrapers disabled. Run: pip install python-jobspy")


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

def _safe_str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _parse_jobspy_date(val) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    raw = str(val).strip().lower()
    try:
        return datetime.fromisoformat(raw[:19])
    except ValueError:
        pass
    m = re.search(r"(\d+)\s+day", raw)
    if m:
        return datetime.utcnow() - timedelta(days=int(m.group(1)))
    m = re.search(r"(\d+)\s+hour", raw)
    if m:
        return datetime.utcnow() - timedelta(hours=int(m.group(1)))
    return None


# ──────────────────────────────────────────────
# Individual source wrappers
# ──────────────────────────────────────────────

def _scrape_source(site: str, query: str, hours_old: int = 24) -> List[JobPosting]:
    """Call jobspy for one site + one query string."""
    if not JOBSPY_AVAILABLE:
        return []
    try:
        df = scrape_jobs(
            site_name=[site],
            search_term=query,
            location="United States",
            results_wanted=50,
            hours_old=hours_old,
            country_indeed="USA",
        )
    except Exception as e:
        logger.warning(f"[jobspy:{site}] Error scraping {query!r}: {e}")
        return []

    if df is None or df.empty:
        return []

    postings: List[JobPosting] = []
    source_label = {
        "linkedin":    "LinkedIn",
        "indeed":      "Indeed",
        "zip_recruiter": "ZipRecruiter",
        "glassdoor":   "Glassdoor",
    }.get(site, site.capitalize())

    for _, row in df.iterrows():
        title    = _safe_str(row.get("title"))
        company  = _safe_str(row.get("company"))
        location = _safe_str(row.get("location")) or "United States"
        url      = _safe_str(row.get("job_url")) or _safe_str(row.get("job_url_direct"))
        snippet  = _safe_str(row.get("description", ""))[:400]
        salary   = _safe_str(row.get("min_amount")) or "Not specified"
        job_type = _safe_str(row.get("job_type")) or "Not specified"
        skills_raw = row.get("skills") or []
        skills   = list(skills_raw) if hasattr(skills_raw, "__iter__") and not isinstance(skills_raw, str) else [query]
        date_val = row.get("date_posted")

        if not url:
            continue

        postings.append(JobPosting(
            title=title or "Unknown",
            company=company or "Company Confidential",
            location=location,
            posted_date=_parse_jobspy_date(date_val),
            apply_url=url,
            source=source_label,
            skills=skills,
            description_snippet=snippet,
            salary=salary,
            job_type=job_type,
            full_description=_safe_str(row.get("description", "")),
        ))

    logger.info(f"[jobspy:{site}] {len(postings)} postings for {query!r}")
    return postings


# ──────────────────────────────────────────────
# Public helpers — called from scrapers/__init__
# ──────────────────────────────────────────────

def scrape_linkedin(query: str) -> List[JobPosting]:
    return _scrape_source("linkedin", query)

def scrape_indeed(query: str) -> List[JobPosting]:
    return _scrape_source("indeed", query)

def scrape_ziprecruiter(query: str) -> List[JobPosting]:
    return _scrape_source("zip_recruiter", query)

def scrape_glassdoor(query: str) -> List[JobPosting]:
    return _scrape_source("glassdoor", query)


# ──────────────────────────────────────────────
# Thin scraper classes (conform to BaseScraper interface)
# ──────────────────────────────────────────────

from .base import BaseScraper   # noqa: E402

class LinkedInScraper(BaseScraper):
    SOURCE_NAME = "LinkedIn"
    def scrape(self, query: str) -> List[JobPosting]:
        return scrape_linkedin(query)

class IndeedScraper(BaseScraper):
    SOURCE_NAME = "Indeed"
    def scrape(self, query: str) -> List[JobPosting]:
        return scrape_indeed(query)

class ZipRecruiterScraper(BaseScraper):
    SOURCE_NAME = "ZipRecruiter"
    def scrape(self, query: str) -> List[JobPosting]:
        return scrape_ziprecruiter(query)

class GlassdoorScraper(BaseScraper):
    SOURCE_NAME = "Glassdoor"
    def scrape(self, query: str) -> List[JobPosting]:
        return scrape_glassdoor(query)

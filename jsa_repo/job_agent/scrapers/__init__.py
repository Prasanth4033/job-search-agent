from .randstad import RandstadScraper
from .manpower import ManpowerScraper
from .kelly import KellyScraper
from .teamlease import TeamLeaseScraper
from .abc_consultants import ABCConsultantsScraper
from .dice import DiceScraper
from .cybercoders import CyberCodersScraper
from .jobspy_scraper import LinkedInScraper, IndeedScraper, ZipRecruiterScraper, GlassdoorScraper
from .base import JobPosting

# Active scrapers — sources that are currently reachable and returning results.
# Disabled: RandstadScraper (401/410), KellyScraper (DNS fail),
#           TeamLeaseScraper (403), ABCConsultantsScraper (connection reset)
ALL_SCRAPERS = [
    DiceScraper,          # Dice.com — HTML scraping
    LinkedInScraper,      # LinkedIn via jobspy
    IndeedScraper,        # Indeed via jobspy
    ZipRecruiterScraper,  # ZipRecruiter via jobspy
    GlassdoorScraper,     # Glassdoor via jobspy
    ManpowerScraper,      # ManpowerGroup JSON API
    CyberCodersScraper,   # CyberCoders HTML
]

# Inactive scrapers — kept in codebase, disabled due to blocks/DNS failures.
# Re-enable by adding back to ALL_SCRAPERS.
INACTIVE_SCRAPERS = [
    RandstadScraper,      # 401 on API, 410 on HTML pages
    KellyScraper,         # DNS resolution failure
    TeamLeaseScraper,     # 403 Forbidden
    ABCConsultantsScraper,# Connection reset
]

__all__ = [
    "RandstadScraper",
    "ManpowerScraper",
    "KellyScraper",
    "TeamLeaseScraper",
    "ABCConsultantsScraper",
    "DiceScraper",
    "CyberCodersScraper",
    "LinkedInScraper",
    "IndeedScraper",
    "ZipRecruiterScraper",
    "GlassdoorScraper",
    "JobPosting",
    "ALL_SCRAPERS",
    "INACTIVE_SCRAPERS",
]

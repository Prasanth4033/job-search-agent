from .randstad import RandstadScraper
from .manpower import ManpowerScraper
from .kelly import KellyScraper
from .teamlease import TeamLeaseScraper
from .abc_consultants import ABCConsultantsScraper
from .dice import DiceScraper
from .cybercoders import CyberCodersScraper
from .jobspy_scraper import LinkedInScraper, IndeedScraper, ZipRecruiterScraper, GlassdoorScraper
from .base import JobPosting

ALL_SCRAPERS = [
    DiceScraper,
    LinkedInScraper,
    IndeedScraper,
    ZipRecruiterScraper,
    GlassdoorScraper,
    RandstadScraper,
    ManpowerScraper,
    KellyScraper,
    CyberCodersScraper,
    TeamLeaseScraper,
    ABCConsultantsScraper,
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
]

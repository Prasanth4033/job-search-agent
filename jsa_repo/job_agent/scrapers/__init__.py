from .randstad import RandstadScraper
from .manpower import ManpowerScraper
from .kelly import KellyScraper
from .teamlease import TeamLeaseScraper
from .abc_consultants import ABCConsultantsScraper
from .base import JobPosting

ALL_SCRAPERS = [
    RandstadScraper,
    ManpowerScraper,
    KellyScraper,
    TeamLeaseScraper,
    ABCConsultantsScraper,
]

__all__ = [
    "RandstadScraper",
    "ManpowerScraper",
    "KellyScraper",
    "TeamLeaseScraper",
    "ABCConsultantsScraper",
    "JobPosting",
    "ALL_SCRAPERS",
]

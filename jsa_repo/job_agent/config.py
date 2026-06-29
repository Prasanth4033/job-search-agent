"""
Configuration loader for Job Search Agent.
Reads from config.yaml and environment variables (.env).
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.yaml"


def load_config() -> dict:
    """Load and merge YAML config with environment variable overrides."""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"config.yaml not found at {CONFIG_FILE}. "
            "Copy config.example.yaml to config.yaml and fill in your values."
        )

    with open(CONFIG_FILE, "r") as f:
        cfg = yaml.safe_load(f) or {}

    # Environment variable overrides (take precedence over YAML)
    cfg.setdefault("email", {})
    cfg["email"]["smtp_host"]     = os.getenv("SMTP_HOST",     cfg["email"].get("smtp_host", "smtp.gmail.com"))
    cfg["email"]["smtp_port"]     = int(os.getenv("SMTP_PORT", cfg["email"].get("smtp_port", 587)))
    cfg["email"]["sender"]        = os.getenv("EMAIL_SENDER",  cfg["email"].get("sender", ""))
    cfg["email"]["password"]      = os.getenv("EMAIL_PASSWORD", cfg["email"].get("password", ""))
    cfg["email"]["recipient"]     = os.getenv("EMAIL_RECIPIENT", cfg["email"].get("recipient", ""))

    return cfg


# Skill keywords used across all scrapers
SKILL_QUERIES = [
    "AWS Data Engineer",
    "GCP Data Engineer",
    "SQL Developer",
    "PL/SQL Developer",
    "Hadoop Data Engineer",
    "Big Data Engineer",
    "PySpark Developer",
    "Hive Developer",
    "Spark Engineer",
    "ETL Developer Hadoop",
]

# US location keywords for filtering
US_LOCATION_KEYWORDS = [
    "united states", "usa", "us", "remote", "anywhere",
    # State abbreviations
    "al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia",
    "ks","ky","la","me","md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj",
    "nm","ny","nc","nd","oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt",
    "va","wa","wv","wi","wy","dc",
    # Common US cities
    "new york","los angeles","chicago","houston","phoenix","philadelphia",
    "san antonio","san diego","dallas","san jose","austin","jacksonville",
    "fort worth","columbus","charlotte","indianapolis","san francisco","seattle",
    "denver","washington","nashville","oklahoma city","el paso","boston",
    "portland","las vegas","memphis","louisville","baltimore","milwaukee",
]

# Source definitions
SOURCES = {
    "Randstad USA": {
        "base_url": "https://www.randstadusa.com",
        "search_path": "/jobs/q-{query}/l-united-states/",
        "enabled": True,
        "note": "Primary US staffing agency — strong coverage.",
    },
    "ManpowerGroup": {
        "base_url": "https://www.manpower.com",
        "search_path": "/ManpowerUSA/JobSearch/?keyword={query}&location=United+States",
        "enabled": True,
        "note": "Major US staffing agency.",
    },
    "Kelly Services": {
        "base_url": "https://jobs.kellyservices.com",
        "search_path": "/us/en/search-results?keywords={query}&country=us",
        "enabled": True,
        "note": "US-based staffing — JavaScript-heavy, uses search fallback.",
    },
    "TeamLease Digital": {
        "base_url": "https://www.teamleasedigital.com",
        "search_path": "/job-seeker/job-listing?skill={query}&location=USA",
        "enabled": True,
        "note": "India-based staffing with some US client placements. Coverage may be limited.",
    },
    "ABC Consultants": {
        "base_url": "https://www.abcconsultants.com",
        "search_path": "/jobs?q={query}&location=United+States",
        "enabled": True,
        "note": "India-based staffing. US job volume will be low; results included where available.",
    },
}

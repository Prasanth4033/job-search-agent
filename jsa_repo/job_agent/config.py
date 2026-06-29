"""
Configuration loader for Job Search Agent — v2.
Reads from config.yaml and environment variables (.env).
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR    = Path(__file__).resolve().parent.parent
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

    # Email / SMTP settings
    cfg.setdefault("email", {})
    cfg["email"]["smtp_host"]  = os.getenv("SMTP_HOST",       cfg["email"].get("smtp_host", "smtp.gmail.com"))
    cfg["email"]["smtp_port"]  = int(os.getenv("SMTP_PORT",   cfg["email"].get("smtp_port", 587)))
    cfg["email"]["sender"]     = os.getenv("EMAIL_SENDER",    cfg["email"].get("sender", ""))
    cfg["email"]["password"]   = os.getenv("EMAIL_PASSWORD",  cfg["email"].get("password", ""))
    cfg["email"]["recipient"]  = os.getenv("EMAIL_RECIPIENT", cfg["email"].get("recipient", ""))

    # Gmail API settings (for draft creation)
    cfg.setdefault("gmail_api", {})
    cfg["gmail_api"]["credentials_file"] = os.getenv(
        "GMAIL_CREDENTIALS_FILE",
        cfg["gmail_api"].get("credentials_file", str(BASE_DIR / "credentials.json"))
    )
    cfg["gmail_api"]["token_file"] = os.getenv(
        "GMAIL_TOKEN_FILE",
        cfg["gmail_api"].get("token_file", str(BASE_DIR / "token.json"))
    )

    return cfg


# ──────────────────────────────────────────────
# Skill search queries — v2 expanded set
# ──────────────────────────────────────────────
SKILL_QUERIES = [
    # Cloud / platform
    "AWS Data Engineer",
    "GCP Data Engineer",
    "Databricks Data Engineer",
    "Snowflake Data Engineer",
    # Core title variants
    "Senior Data Engineer",
    "Data Engineer",
    # Specific skills
    "SQL Developer",
    "PL/SQL Developer",
    "PySpark Developer",
    "Spark Engineer",
    # Big Data
    "Hadoop Data Engineer",
    "Big Data Engineer",
    "ETL Developer Hadoop",
    "Hive Developer",
]

# ──────────────────────────────────────────────
# US location keywords for filtering
# ──────────────────────────────────────────────
US_LOCATION_KEYWORDS = [
    "united states", "usa", "us", "remote", "anywhere",
    "al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia",
    "ks","ky","la","me","md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj",
    "nm","ny","nc","nd","oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt",
    "va","wa","wv","wi","wy","dc",
    "new york","los angeles","chicago","houston","phoenix","philadelphia",
    "san antonio","san diego","dallas","san jose","austin","jacksonville",
    "fort worth","columbus","charlotte","indianapolis","san francisco","seattle",
    "denver","washington","nashville","oklahoma city","el paso","boston",
    "portland","las vegas","memphis","louisville","baltimore","milwaukee",
]

# ──────────────────────────────────────────────
# Source catalogue — v2 (11 sources)
# ──────────────────────────────────────────────
SOURCES = {
    # ── Top-tier job portals ──
    "Dice": {
        "base_url":    "https://www.dice.com",
        "search_path": "/jobs?q={query}&countryCode=US",
        "enabled":     True,
        "note":        "Tech-focused US portal — excellent DE/SQL/AWS coverage. Uses JSON API.",
    },
    "LinkedIn": {
        "base_url":    "https://www.linkedin.com",
        "search_path": "/jobs/search/?keywords={query}&location=United+States",
        "enabled":     True,
        "note":        "World's largest professional network. Scraped via python-jobspy.",
    },
    "Indeed": {
        "base_url":    "https://www.indeed.com",
        "search_path": "/jobs?q={query}&l=United+States",
        "enabled":     True,
        "note":        "Largest general job board. Scraped via python-jobspy.",
    },
    "ZipRecruiter": {
        "base_url":    "https://www.ziprecruiter.com",
        "search_path": "/jobs-search?search={query}&location=United+States",
        "enabled":     True,
        "note":        "High-volume US job board. Scraped via python-jobspy.",
    },
    "Glassdoor": {
        "base_url":    "https://www.glassdoor.com",
        "search_path": "/Job/jobs.htm?sc.keyword={query}&locT=N&locId=1",
        "enabled":     True,
        "note":        "Salary-transparent job board. Scraped via python-jobspy.",
    },
    # ── Staffing agencies ──
    "Randstad USA": {
        "base_url":    "https://www.randstadusa.com",
        "search_path": "/jobs/q-{query}/l-united-states/",
        "enabled":     True,
        "note":        "Primary US staffing agency. Uses internal JSON API.",
    },
    "ManpowerGroup": {
        "base_url":    "https://www.manpower.com",
        "search_path": "/ManpowerUSA/JobSearch/?keyword={query}&location=United+States",
        "enabled":     True,
        "note":        "Major US staffing agency.",
    },
    "Kelly Services": {
        "base_url":    "https://jobs.kellyservices.com",
        "search_path": "/us/en/search-results?keywords={query}&country=us",
        "enabled":     True,
        "note":        "US staffing — Phenom People SPA, uses JSON API.",
    },
    "CyberCoders": {
        "base_url":    "https://www.cybercoders.com",
        "search_path": "/search/?searchterms={query}&location=United+States",
        "enabled":     True,
        "note":        "Tech-focused US staffing firm.",
    },
    "TeamLease Digital": {
        "base_url":    "https://www.teamleasedigital.com",
        "search_path": "/job-seeker/job-listing?skill={query}&location=USA",
        "enabled":     True,
        "note":        "India-based staffing with US client placements.",
    },
    "ABC Consultants": {
        "base_url":    "https://www.abcconsultants.com",
        "search_path": "/jobs?q={query}&location=United+States",
        "enabled":     True,
        "note":        "India-based staffing. US volume may be low.",
    },
}

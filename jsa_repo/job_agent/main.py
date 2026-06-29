"""
Job Search Agent — main entry point.

Usage:
  # Run once immediately
  python -m job_agent.main

  # Run with custom hours window
  python -m job_agent.main --hours 48

  # Skip email, save HTML report only
  python -m job_agent.main --no-email

  # Daemon mode — runs daily at configured time
  python -m job_agent.main --daemon
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List

import schedule

from .config import load_config, SKILL_QUERIES, ALL_SCRAPERS
from .scrapers.base import JobPosting
from .scrapers import ALL_SCRAPERS as SCRAPER_CLASSES
from .filters import filter_us_only, filter_recent
from .notifiers import EmailNotifier, save_report
from .utils.logger import logger


# ──────────────────────────────────────────────
# Core pipeline
# ──────────────────────────────────────────────

def run_scraper(scraper_cls, skill_queries: List[str]) -> List[JobPosting]:
    """Instantiate and run a single scraper. Returns raw postings."""
    scraper = scraper_cls()
    return scraper.scrape_all_skills(skill_queries)


def fetch_all_jobs(skill_queries: List[str], max_workers: int = 3) -> List[JobPosting]:
    """
    Run all scrapers in parallel (bounded thread pool).
    Returns the raw combined list before any filtering.
    """
    all_postings: List[JobPosting] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(run_scraper, cls, skill_queries): cls.SOURCE_NAME
            for cls in SCRAPER_CLASSES
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                results = future.result()
                logger.info(f"[{source}] Fetched {len(results)} raw postings.")
                all_postings.extend(results)
            except Exception as e:
                logger.error(f"[{source}] Scraper raised exception: {e}")
    return all_postings


def run_pipeline(cfg: dict, hours: int = 24, send_email: bool = True) -> List[JobPosting]:
    """
    Full pipeline:
      1. Fetch jobs from all sources in parallel.
      2. Filter to US + last N hours.
      3. Deduplicate by URL.
      4. Save HTML report.
      5. Send email (unless disabled).
    """
    run_date = datetime.utcnow()
    logger.info(f"=== Job Search Agent — {run_date.strftime('%Y-%m-%d %H:%M UTC')} ===")
    logger.info(f"Targeting skills: {', '.join(SKILL_QUERIES)}")

    # 1 — fetch
    raw = fetch_all_jobs(SKILL_QUERIES)
    logger.info(f"Total raw postings across all sources: {len(raw)}")

    # 2 — filter location
    us_only = filter_us_only(raw)
    logger.info(f"After US location filter: {len(us_only)}")

    # 3 — filter recency
    recent = filter_recent(us_only, hours=hours)
    logger.info(f"After {hours}-hour recency filter: {len(recent)}")

    # 4 — deduplicate
    seen: set = set()
    unique: List[JobPosting] = []
    for p in recent:
        if p.apply_url not in seen:
            seen.add(p.apply_url)
            unique.append(p)
    logger.info(f"After deduplication: {len(unique)} unique postings")

    # 5 — save HTML report
    report_path = save_report(unique, run_date)
    logger.info(f"Report → {report_path}")

    # 6 — send email
    if send_email:
        try:
            notifier = EmailNotifier(cfg)
            notifier.send(unique, run_date)
        except ValueError as e:
            logger.warning(f"Email skipped: {e}")
    else:
        logger.info("Email delivery skipped (--no-email flag).")

    logger.info(f"=== Run complete. {len(unique)} job(s) delivered. ===\n")
    return unique


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Daily Data Engineering Job Search Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--hours", type=int, default=24,
        help="Only include jobs posted within this many hours (default: 24).",
    )
    parser.add_argument(
        "--no-email", action="store_true",
        help="Save HTML report only — do not send email.",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Run in daemon mode — execute daily at the time set in config.yaml.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg  = load_config()

    if args.daemon:
        run_time = cfg.get("schedule", {}).get("run_time", "07:00")
        logger.info(f"Daemon mode — scheduling daily run at {run_time} UTC.")

        def _job():
            run_pipeline(cfg, hours=args.hours, send_email=not args.no_email)

        schedule.every().day.at(run_time).do(_job)
        _job()   # Run immediately on startup
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_pipeline(cfg, hours=args.hours, send_email=not args.no_email)


if __name__ == "__main__":
    main()

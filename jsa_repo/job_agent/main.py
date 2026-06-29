"""
Job Search Agent — main entry point. v2.

Usage:
  python -m job_agent.main                    # Run once immediately
  python -m job_agent.main --hours 48         # Custom recency window
  python -m job_agent.main --no-email         # Skip summary email
  python -m job_agent.main --no-drafts        # Skip Gmail drafts
  python -m job_agent.main --daemon           # Daily scheduled mode
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List

import schedule

from .config import load_config, SKILL_QUERIES
from .scrapers.base import JobPosting
from .scrapers import ALL_SCRAPERS as SCRAPER_CLASSES
from .filters import filter_us_only, filter_recent
from .notifiers import EmailNotifier, save_report
from .notifiers.draft_creator import create_draft
from .resume.generator import generate_resume
from .utils.logger import logger


# ──────────────────────────────────────────────
# Core pipeline helpers
# ──────────────────────────────────────────────

def run_scraper(scraper_cls, skill_queries: List[str]) -> List[JobPosting]:
    scraper = scraper_cls()
    return scraper.scrape_all_skills(skill_queries)


def fetch_all_jobs(skill_queries: List[str], max_workers: int = 4) -> List[JobPosting]:
    """Run all scrapers in parallel. Returns combined raw postings."""
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


# ──────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────

def run_pipeline(
    cfg: dict,
    hours: int = 24,
    send_email: bool = True,
    create_drafts: bool = True,
) -> List[JobPosting]:
    """
    Full v2 pipeline:
      1.  Fetch jobs from all 11 sources in parallel.
      2.  Filter to US + last N hours.
      3.  Deduplicate by URL.
      4.  For each job: generate ATS-tailored .docx resume.
      5.  For each job: create Gmail draft with resume attached.
      6.  Save HTML summary report.
      7.  Send summary email (optional).
    """
    run_date = datetime.utcnow()
    logger.info(f"=== Job Search Agent v2 — {run_date.strftime('%Y-%m-%d %H:%M UTC')} ===")
    logger.info(f"Skills: {', '.join(SKILL_QUERIES)}")

    # ── 1. Fetch ──────────────────────────────
    raw = fetch_all_jobs(SKILL_QUERIES)
    logger.info(f"Total raw postings: {len(raw)}")

    # ── 2. Filter location ────────────────────
    us_only = filter_us_only(raw)
    logger.info(f"After US location filter: {len(us_only)}")

    # ── 3. Filter recency ─────────────────────
    recent = filter_recent(us_only, hours=hours)
    logger.info(f"After {hours}-hour recency filter: {len(recent)}")

    # ── 4. Deduplicate ────────────────────────
    seen: set = set()
    unique: List[JobPosting] = []
    for p in recent:
        if p.apply_url not in seen:
            seen.add(p.apply_url)
            unique.append(p)
    logger.info(f"After deduplication: {len(unique)} unique postings")

    if not unique:
        logger.info("No new jobs found — skipping resume/draft generation.")
    else:
        # ── 5. Generate resumes + 6. Create Gmail drafts ──
        drafts_created = 0
        for i, job in enumerate(unique, 1):
            logger.info(f"[{i}/{len(unique)}] Processing: {job.title} @ {job.company}")
            jd_text = job.full_description or job.description_snippet or job.title

            # Generate tailored resume
            try:
                resume_path, matched = generate_resume(
                    job_title=job.title,
                    company=job.company,
                    jd_text=jd_text,
                )
                job.resume_path    = str(resume_path)
                job.matched_skills = matched
                logger.info(f"  Resume: {resume_path.name} | Matched skills: {len(matched)}")
            except Exception as e:
                logger.error(f"  Resume generation failed: {e}")
                resume_path = None

            # Create Gmail draft
            if create_drafts:
                try:
                    ok = create_draft(job, resume_path=resume_path)
                    if ok:
                        drafts_created += 1
                except Exception as e:
                    logger.error(f"  Draft creation failed: {e}")

        logger.info(f"Gmail drafts created: {drafts_created}/{len(unique)}")

    # ── 7. Save HTML report ───────────────────
    report_path = save_report(unique, run_date)
    logger.info(f"HTML report: {report_path}")

    # ── 8. Send summary email ─────────────────
    if send_email:
        try:
            notifier = EmailNotifier(cfg)
            notifier.send(unique, run_date)
        except ValueError as e:
            logger.warning(f"Summary email skipped: {e}")
    else:
        logger.info("Summary email skipped (--no-email).")

    logger.info(f"=== Run complete. {len(unique)} job(s) processed. ===\n")
    return unique


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Daily Data Engineering Job Search Agent v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--hours", type=int, default=24,
        help="Only include jobs posted within this many hours (default: 24).",
    )
    parser.add_argument(
        "--no-email", action="store_true",
        help="Skip the summary email — HTML report still saved.",
    )
    parser.add_argument(
        "--no-drafts", action="store_true",
        help="Skip Gmail draft creation — resumes still generated.",
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
            run_pipeline(
                cfg,
                hours=args.hours,
                send_email=not args.no_email,
                create_drafts=not args.no_drafts,
            )

        schedule.every().day.at(run_time).do(_job)
        _job()   # Run immediately on startup
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        run_pipeline(
            cfg,
            hours=args.hours,
            send_email=not args.no_email,
            create_drafts=not args.no_drafts,
        )


if __name__ == "__main__":
    main()

"""
HTML report generator.
Builds a self-contained, styled HTML report of job postings
and saves it to the reports/ directory.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ..scrapers.base import JobPosting
from ..utils.logger import logger

REPORT_DIR = Path(__file__).resolve().parent.parent.parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# Colour palette per source
SOURCE_COLOURS: Dict[str, str] = {
    "Randstad USA":      "#e9f5fb",
    "ManpowerGroup":     "#fdf3e7",
    "Kelly Services":    "#f0faf0",
    "TeamLease Digital": "#fdf0fb",
    "ABC Consultants":   "#fff8e7",
}
SOURCE_BADGE_COLOURS: Dict[str, str] = {
    "Randstad USA":      "#1565c0",
    "ManpowerGroup":     "#e65100",
    "Kelly Services":    "#2e7d32",
    "TeamLease Digital": "#6a1b9a",
    "ABC Consultants":   "#f57f17",
}


def _skill_badges(skills: List[str]) -> str:
    badges = "".join(
        f'<span style="background:#e3f2fd;color:#1565c0;padding:2px 8px;'
        f'border-radius:12px;font-size:11px;margin:2px;display:inline-block;">'
        f'{s}</span>'
        for s in skills
    )
    return badges


def build_html_report(postings: List[JobPosting], run_date: datetime) -> str:
    """Generate and return the full HTML string."""
    by_source: Dict[str, List[JobPosting]] = {}
    for p in postings:
        by_source.setdefault(p.source, []).append(p)

    date_str = run_date.strftime("%A, %B %d, %Y")
    count    = len(postings)

    # ── summary cards ─────────────────────────────────
    summary_cards = ""
    for source, jobs in by_source.items():
        colour = SOURCE_BADGE_COLOURS.get(source, "#555")
        summary_cards += (
            f'<div style="background:{colour};color:#fff;padding:14px 20px;'
            f'border-radius:8px;text-align:center;min-width:140px;">'
            f'<div style="font-size:28px;font-weight:700;">{len(jobs)}</div>'
            f'<div style="font-size:12px;margin-top:4px;">{source}</div></div>'
        )

    # ── job cards ────────────────────────────────────
    job_cards = ""
    for source, jobs in by_source.items():
        bg     = SOURCE_COLOURS.get(source, "#fafafa")
        badge  = SOURCE_BADGE_COLOURS.get(source, "#555")
        job_cards += (
            f'<h2 style="margin:28px 0 10px;font-size:16px;color:#333;'
            f'border-bottom:2px solid {badge};padding-bottom:6px;">'
            f'{source} &nbsp;<span style="font-size:13px;color:#666;font-weight:400;">'
            f'({len(jobs)} posting{"s" if len(jobs)!=1 else ""})</span></h2>'
        )
        for j in jobs:
            posted_str = (
                j.posted_date.strftime("%b %d, %Y %H:%M UTC") if j.posted_date else "Date unknown"
            )
            skill_html = _skill_badges(j.skills)
            job_cards += f"""
<div style="background:{bg};border:1px solid #e0e0e0;border-radius:8px;
            padding:16px;margin-bottom:12px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
    <div>
      <a href="{j.apply_url}" style="font-size:15px;font-weight:600;color:#1a237e;text-decoration:none;">
        {j.title}
      </a>
      <div style="font-size:12px;color:#555;margin-top:3px;">
        📍 {j.location} &nbsp;·&nbsp; 🏢 {j.company}
        &nbsp;·&nbsp; 🕐 {posted_str}
      </div>
    </div>
    <a href="{j.apply_url}" style="background:{badge};color:#fff;padding:7px 16px;
       border-radius:5px;font-size:12px;text-decoration:none;white-space:nowrap;
       margin-top:4px;">Apply Now →</a>
  </div>
  {'<div style="margin-top:8px;font-size:12px;color:#444;">'+j.description_snippet+'</div>' if j.description_snippet else ''}
  <div style="margin-top:8px;">{skill_html}</div>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Daily Data Engineering Jobs — {date_str}</title>
</head>
<body style="font-family:'Segoe UI',Arial,sans-serif;margin:0;padding:20px;background:#f5f7fa;color:#222;">
<div style="max-width:860px;margin:0 auto;">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1a237e 0%,#283593 100%);
              color:#fff;padding:24px 28px;border-radius:10px 10px 0 0;">
    <h1 style="margin:0;font-size:22px;">📊 Daily Data Engineering Job Report</h1>
    <p style="margin:6px 0 0;font-size:13px;opacity:.85;">{date_str} &nbsp;·&nbsp; US Locations &nbsp;·&nbsp; Last 24 Hours</p>
  </div>

  <!-- Stats banner -->
  <div style="background:#fff;padding:20px 28px;border:1px solid #ddd;">
    <p style="margin:0 0 12px;font-size:14px;color:#555;">
      <strong>{count}</strong> new posting{"s" if count!=1 else ""} found across all sources.
      Skills targeted: AWS Data Engineer · GCP Data Engineer · SQL Developer · PL/SQL · Hadoop · Spark · PySpark
    </p>
    <div style="display:flex;flex-wrap:wrap;gap:10px;">{summary_cards}</div>
  </div>

  <!-- Job listings -->
  <div style="background:#fff;padding:20px 28px;border:1px solid #ddd;border-top:none;border-radius:0 0 10px 10px;">
    {job_cards if job_cards else '<p style="color:#888;text-align:center;padding:40px 0;">No new postings found in the last 24 hours. Check back tomorrow.</p>'}
  </div>

  <!-- Footer -->
  <p style="font-size:11px;color:#aaa;text-align:center;margin-top:16px;">
    Generated by Job Search Agent v1.0.0 &nbsp;·&nbsp;
    Sources: Randstad USA, ManpowerGroup, Kelly Services, TeamLease Digital, ABC Consultants &nbsp;·&nbsp;
    <em>TeamLease and ABC Consultants are India-based; US listings may be limited.</em>
  </p>
</div>
</body>
</html>"""
    return html


def save_report(postings: List[JobPosting], run_date: datetime) -> Path:
    """Write the HTML report to disk and return the file path."""
    html    = build_html_report(postings, run_date)
    fname   = REPORT_DIR / f"job_report_{run_date.strftime('%Y-%m-%d')}.html"
    fname.write_text(html, encoding="utf-8")
    logger.info(f"HTML report saved → {fname}")
    return fname

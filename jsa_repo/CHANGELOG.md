# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] — 2026-06-29

### Added
- Initial production release.
- Scrapers for Randstad USA, ManpowerGroup, Kelly Services, TeamLease Digital, ABC Consultants.
- US-only location filter with explicit India/Canada/UK rejection patterns.
- 24-hour recency filter (configurable via `--hours` flag).
- Parallel scraper execution via `ThreadPoolExecutor`.
- Styled HTML report saved to `reports/` directory.
- Gmail SMTP email delivery with HTML + plain-text fallback.
- Daemon mode (`--daemon`) with configurable daily schedule via `schedule` library.
- `BaseScraper` abstract class with retry/backoff, throttling, and session management.
- JSON API primary path + HTML BeautifulSoup fallback for all scrapers.
- `loguru`-based logging with rotating file output (10 MB, 7-day retention).
- Full unit test suite for location and recency filters.
- `scripts/setup.sh` one-time environment bootstrap.
- Production documentation: README, ARCHITECTURE, CONFIGURATION, DEPLOYMENT, CONTRIBUTING.
- `.gitignore` covering secrets, runtime output, and Python build artefacts.

---

## [Unreleased]

### Planned
- Slack / Microsoft Teams notification channel.
- SQLite job-seen cache to suppress duplicate alerts across days.
- LinkedIn and Indeed integration for broader US coverage.
- Docker Compose setup for zero-config server deployment.
- Weekly digest mode (top 20 roles of the week).
- Keyword relevance scoring to surface the best-match postings first.

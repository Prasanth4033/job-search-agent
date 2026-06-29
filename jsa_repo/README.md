# 📊 Job Search Agent

> **Daily, automated Data Engineering job discovery** — fetches US-based postings from the last 24 hours across major staffing agencies and delivers a formatted HTML report to your Gmail inbox every morning at 7 AM.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Production](https://img.shields.io/badge/Status-Production-green)]()

---

## 🎯 What It Does

| Feature | Detail |
|---|---|
| **Sources** | Randstad USA, ManpowerGroup, Kelly Services, TeamLease Digital, ABC Consultants |
| **Skills** | AWS Data Engineer · GCP Data Engineer · SQL Developer · PL/SQL · Hadoop · Spark · PySpark · Hive |
| **Location** | United States only (all 50 states + DC, Remote-US) |
| **Freshness** | Last 24 hours (configurable) |
| **Schedule** | Daily at 07:00 UTC (configurable) |
| **Delivery** | HTML email → Gmail + local HTML report |

> **Note on India-based sources:** TeamLease Digital and ABC Consultants are India-headquartered staffing firms. Their US job listings are limited. They are included to capture any US client placements they publish, but expect lower volume from these two sources vs. Randstad, ManpowerGroup, and Kelly.

---

## 🚀 Quick Start

### 1 — Clone and set up

```bash
git clone https://github.com/<your-username>/job-search-agent.git
cd job-search-agent
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2 — Configure

```bash
# Edit config.yaml — review schedule, skills, sources
nano config.yaml

# Edit .env — add your Gmail App Password
nano .env
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for a complete guide.

### 3 — Run

```bash
# Single run (fetch + email)
./scripts/run.sh

# Single run, no email (save HTML report only)
./scripts/run.sh --no-email

# Expand window to 48 hours
./scripts/run.sh --hours 48

# Daemon mode — runs daily at 07:00 UTC automatically
./scripts/run.sh --daemon
```

---

## 📁 Project Structure

```
job-search-agent/
├── job_agent/
│   ├── main.py              ← Entry point & pipeline orchestrator
│   ├── config.py            ← Config loader (YAML + env vars)
│   ├── scrapers/
│   │   ├── base.py          ← JobPosting dataclass + BaseScraper
│   │   ├── randstad.py      ← Randstad USA scraper
│   │   ├── manpower.py      ← ManpowerGroup scraper (API + HTML)
│   │   ├── kelly.py         ← Kelly Services scraper (API + HTML)
│   │   ├── teamlease.py     ← TeamLease Digital (US-filtered)
│   │   └── abc_consultants.py ← ABC Consultants (US-filtered)
│   ├── filters/
│   │   ├── location.py      ← US-only location filter
│   │   └── recency.py       ← 24-hour recency filter
│   ├── notifiers/
│   │   ├── html_reporter.py ← Styled HTML report builder
│   │   └── email_notifier.py← Gmail SMTP delivery
│   └── utils/
│       └── logger.py        ← Loguru logging (console + rotating file)
├── tests/
│   └── test_filters.py      ← Unit tests for filters
├── scripts/
│   ├── setup.sh             ← One-time environment setup
│   └── run.sh               ← Run wrapper
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   └── DEPLOYMENT.md
├── config.example.yaml      ← Config template (copy → config.yaml)
├── .env.example             ← Secrets template (copy → .env)
├── requirements.txt
└── README.md
```

---

## ⚙️ Gmail App Password Setup

This agent sends email via Gmail SMTP using an **App Password** (not your account password).

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already on
3. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
4. Create an App Password — name it "Job Search Agent"
5. Copy the 16-character password into your `.env`:

```
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_RECIPIENT=gspr4033@gmail.com
```

---

## 🔄 Pipeline Overview

```
┌──────────────────────────────────────────────────────┐
│  Scheduler (07:00 UTC daily)                         │
└──────────────────┬───────────────────────────────────┘
                   │
    ┌──────────────▼──────────────┐
    │  Parallel Scraper Threads   │
    │  ┌─────────┐ ┌───────────┐  │
    │  │Randstad │ │ManpowerGrp│  │
    │  ├─────────┤ ├───────────┤  │
    │  │  Kelly  │ │TeamLease  │  │
    │  ├─────────┤ ├───────────┤  │
    │  │   ABC   │ │           │  │
    │  └─────────┘ └───────────┘  │
    └──────────────┬──────────────┘
                   │ raw postings
    ┌──────────────▼──────────────┐
    │  Location Filter (US only)  │
    └──────────────┬──────────────┘
                   │
    ┌──────────────▼──────────────┐
    │  Recency Filter (≤ 24 hrs)  │
    └──────────────┬──────────────┘
                   │
    ┌──────────────▼──────────────┐
    │  Deduplication (by URL)     │
    └──────────────┬──────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
  ┌──────▼──────┐    ┌───────▼──────┐
  │ HTML Report │    │  Gmail Email │
  │  (reports/) │    │   (SMTP TLS) │
  └─────────────┘    └──────────────┘
```

---

## 🧪 Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

---

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md).

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT — see [LICENSE](LICENSE).

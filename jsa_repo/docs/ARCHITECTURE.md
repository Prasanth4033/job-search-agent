# Architecture

## Design Principles

1. **Single responsibility** — each module does one thing (scrape, filter, notify).
2. **Fail gracefully** — a scraper failure never stops the rest of the pipeline.
3. **Parallel by default** — all scrapers run concurrently in a bounded thread pool.
4. **Zero secrets in code** — credentials live in `.env`, never in source files.
5. **Observable** — every step is logged (console + rotating file); errors are distinct from warnings.

---

## Component Map

```
┌─────────────────────────────────────────────────────────────────┐
│  job_agent/main.py  (pipeline orchestrator)                     │
│                                                                 │
│   run_pipeline()                                                │
│   ├── fetch_all_jobs()   ──►  ThreadPoolExecutor               │
│   │                              ├── RandstadScraper           │
│   │                              ├── ManpowerScraper           │
│   │                              ├── KellyScraper              │
│   │                              ├── TeamLeaseScraper          │
│   │                              └── ABCConsultantsScraper     │
│   ├── filter_us_only()   ──►  filters/location.py              │
│   ├── filter_recent()    ──►  filters/recency.py               │
│   ├── deduplicate()      ──►  (inline, by apply_url)           │
│   ├── save_report()      ──►  notifiers/html_reporter.py       │
│   └── EmailNotifier.send()──► notifiers/email_notifier.py      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Ingestion

Each `BaseScraper` subclass implements `scrape(query: str) -> List[JobPosting]`.

- **Primary path** — JSON API endpoint (where available).
- **Fallback path** — HTML page parsed with BeautifulSoup.
- **Retry logic** — 3 attempts with exponential backoff via `urllib3.Retry`.
- **Throttling** — 1.5–3.5 s random delay between requests per scraper.

### 2. Normalisation

All scrapers return the same `JobPosting` dataclass:

```python
@dataclass
class JobPosting:
    title: str
    company: str
    location: str
    posted_date: Optional[datetime]   # UTC
    apply_url: str                     # Canonical dedup key
    source: str
    skills: List[str]
    description_snippet: str
    salary: str
    job_type: str
```

### 3. Filtering

| Filter | Module | Logic |
|---|---|---|
| US location | `filters/location.py` | Regex match on state abbreviations, "United States", "Remote", etc. Explicitly rejects India/Canada/UK city names. |
| Recency | `filters/recency.py` | `posted_date` within last N hours. If `posted_date` is `None`, the posting is included optimistically. |
| Deduplication | `main.py` inline | Set of `apply_url` strings. First occurrence wins. |

### 4. Output

| Output | Format | Location |
|---|---|---|
| HTML Report | Self-contained HTML | `reports/job_report_YYYY-MM-DD.html` |
| Email | HTML + plain-text fallback | Gmail inbox via SMTP TLS |
| Logs | Structured text | `logs/job_agent_YYYY-MM-DD.log` |

---

## Concurrency Model

```
main thread
    │
    └── ThreadPoolExecutor(max_workers=3)
            ├── Thread 1: RandstadScraper  (Randstad + ManpowerGroup)
            ├── Thread 2: KellyScraper
            └── Thread 3: TeamLeaseScraper + ABCConsultantsScraper
```

Scrapers are I/O-bound (HTTP). Python's GIL is not a bottleneck here. `max_workers=3` is conservative to avoid triggering rate limits on target sites.

---

## Error Handling Strategy

| Error Type | Behaviour |
|---|---|
| HTTP 4xx / 5xx | Log warning, skip source, continue |
| Connection timeout | Log warning, retry up to 3x with backoff |
| HTML parse error | Log debug, skip individual card |
| Email auth failure | Log error, report saved to disk |
| Config missing | Raise `FileNotFoundError` immediately (fail-fast) |

---

## Extension Points

### Adding a new scraper

1. Create `job_agent/scrapers/my_source.py` inheriting `BaseScraper`.
2. Implement `scrape(query)` and set `SOURCE_NAME`.
3. Add to `job_agent/scrapers/__init__.py` → `ALL_SCRAPERS` list.

### Adding a new notification channel

1. Create `job_agent/notifiers/slack_notifier.py` (or Teams, etc.).
2. Call it from `main.py` → `run_pipeline()` after `EmailNotifier`.

### Changing skill targets

Edit `SKILL_QUERIES` in `job_agent/config.py` or `skills` list in `config.yaml`.
